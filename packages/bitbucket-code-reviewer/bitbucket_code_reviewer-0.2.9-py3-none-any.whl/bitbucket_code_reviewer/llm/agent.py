"""LangChain agent for code review with tool-calling capabilities."""

import json
import time
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..core.models import PullRequestDiff, ReviewConfig
from ..prompts import get_system_prompt
from .tools import create_code_review_tools
from .callbacks import (
    LLMTimingCallback,
    IterationLimitCallback,
    RateLimitRetryCallback,
)


class CodeReviewAgent:
    """LangChain agent for performing code reviews."""

    def __init__(
        self,
        llm: BaseLanguageModel,
        config: ReviewConfig,
        pr_diff: PullRequestDiff,
        previous_comments: list = None,
    ):
        """Initialize the code review agent.

        Args:
            llm: Configured language model
            config: Review configuration
            pr_diff: Pull request diff information
            previous_comments: List of previous bot comments on this PR
        """
        self.llm = llm
        self.config = config
        self.pr_diff = pr_diff
        self.previous_comments = previous_comments or []

        # Create tools with working directory, PR diff, and previous comments
        self.tools = create_code_review_tools(
            config.working_directory, pr_diff, previous_comments, config.verbose
        )

        # Create the agent
        self.agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools.

        Returns:
            Configured agent executor
        """
        try:
            # Get the system prompt
            system_prompt = get_system_prompt()
            
            # Escape curly braces in system prompt for ChatPromptTemplate
            # (it interprets { } as template variables, but our prompt has JSON examples)
            escaped_system_prompt = system_prompt.replace("{", "{{").replace("}", "}}")

            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", escaped_system_prompt),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )
        except Exception as e:
            print(f"❌ ERROR during agent creation: {str(e)}")
            raise

        # Attach per-LLM roundtrip timing and iteration limit callbacks
        try:
            provider_name = getattr(self.config.llm_provider, "value", str(self.config.llm_provider))
            timing_callback = LLMTimingCallback(
                provider_name=provider_name,
                model_name=self.config.model_name,
            )
            # Attach timing callback to LLM (for LLM events)
            instrumented_llm = self.llm.with_config(callbacks=[timing_callback])
        except Exception:
            # Fall back gracefully to the raw LLM if instrumentation fails
            instrumented_llm = self.llm

        # Create the agent
        agent = create_openai_tools_agent(
            llm=instrumented_llm,
            tools=self.tools,
            prompt=prompt,
        )

        # Create the agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,  # Disable verbose output
            max_iterations=self.config.max_tool_iterations,
            max_execution_time=None,  # No time limit, only iteration limit
            early_stopping_method="generate",  # Generate final answer when hitting limit
            handle_parsing_errors=True,
        )
        
        # Attach iteration callback to AgentExecutor (for agent events)
        try:
            iteration_callback = IterationLimitCallback(
                max_iterations=self.config.max_tool_iterations,
                wrap_up_threshold=self.config.wrap_up_threshold
            )
            agent_executor = agent_executor.with_config(callbacks=[iteration_callback])
        except Exception:
            pass  # Continue without iteration tracking if callback fails
        
        return agent_executor

    def _prepare_file_list(self) -> list[dict]:
        """Prepare file list with emojis for template rendering.

        Returns:
            List of file dictionaries with emoji, filename, additions, deletions
        """
        status_emoji_map = {
            "added": "➕",
            "modified": "✏️",
            "removed": "➖",
            "renamed": "📝",
        }

        files = []
        for file_change in self.pr_diff.files:
            files.append(
                {
                    "emoji": status_emoji_map.get(
                        file_change.status, "❓"
                    ),
                    "filename": file_change.filename,
                    "additions": file_change.additions,
                    "deletions": file_change.deletions,
                }
            )
        return files

    def _prepare_previous_comments(self) -> list[dict]:
        """Prepare previous comments for template rendering.

        Returns:
            List of comment dictionaries with location, author, date, content
        """
        prepared_comments = []
        for comment in self.previous_comments:
            comment_location = "General comment"
            if comment.get("file_path"):
                location_str = comment["file_path"]
                if comment.get("line"):
                    location_str += f":{comment['line']}"
                comment_location = f"Inline comment at {location_str}"

            author = comment.get("author", "Unknown")
            
            # Safely handle content (may be None or non-string)
            content_raw = comment.get("content")
            if content_raw is None:
                content = ""
            else:
                content = content_raw if isinstance(content_raw, str) else str(content_raw)
            
            # Cap at 2000 chars to keep context manageable
            content_display = (
                content
                if len(content) <= 2000
                else content[:2000] + "..."
            )

            prepared_comments.append(
                {
                    "location": comment_location,
                    "author": author,
                    "created_date": comment.get("created_date", "Unknown"),
                    "content_display": content_display,
                }
            )
        return prepared_comments

    def _create_initial_message(self) -> str:
        """Create the initial human message with PR context using Jinja2.

        Returns:
            Initial message for the agent
        """
        # Setup Jinja2 environment
        template_dir = (
            Path(__file__).parent.parent / "prompts" / "user" / "templates"
        )
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,  # Plain-text templates, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Prepare template context
        context = {
            "pr_info": self.pr_diff.pull_request,
            "files": self._prepare_file_list(),
            "previous_comments": self._prepare_previous_comments(),
            "file_paths": [f.filename for f in self.pr_diff.files],
        }

        # Render template
        try:
            template = env.get_template("initial_message.j2")
        except TemplateNotFound as e:
            raise FileNotFoundError(
                f"Template 'initial_message.j2' not found in {template_dir}"
            ) from e
        return template.render(context)

    def _sanitize_json_string(self, raw: str) -> str:
        """Best-effort repair of common JSON issues from LLM output.
        
        Args:
            raw: Raw JSON string from LLM
            
        Returns:
            Cleaned JSON string
        """
        # Strip markdown code blocks
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            # Find the first newline after the opening ```
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1 :]
            # Remove trailing ```
            if cleaned.endswith("```"):
                cleaned = cleaned[: -3].rstrip()
        
        return cleaned

    def _validate_json(self, json_string: str) -> tuple[bool, str, str]:
        """Validate JSON and return error details if invalid.
        
        Args:
            json_string: JSON string to validate
            
        Returns:
            Tuple of (is_valid, error_message, error_context)
        """
        try:
            cleaned = self._sanitize_json_string(json_string)
            parsed = json.loads(cleaned)
            
            # Validate required structure
            if "changes" not in parsed:
                return False, "Missing required field 'changes'", ""
            if not isinstance(parsed["changes"], list):
                return False, "Field 'changes' must be a list", ""
            
            return True, "", ""
            
        except json.JSONDecodeError as e:
            # Extract context around the error
            error_pos = e.pos
            context_start = max(0, error_pos - 100)
            context_end = min(len(json_string), error_pos + 100)
            error_context = json_string[context_start:context_end]
            
            error_message = f"JSON parsing error: {e.msg} (line {e.lineno}, column {e.colno})"
            return False, error_message, error_context
            
        except Exception as e:
            return False, f"JSON validation error: {str(e)}", ""

    def _create_retry_feedback(self, error_message: str, error_context: str) -> str:
        """Create feedback message for LLM when JSON parsing fails using Jinja2.
        
        Args:
            error_message: Description of the JSON error
            error_context: Text context around the error
            
        Returns:
            Feedback message for the LLM
        """
        # Setup Jinja2 environment
        template_dir = (
            Path(__file__).parent.parent / "prompts" / "user" / "templates"
        )
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,  # Plain-text templates, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Prepare template context
        context = {
            "error_message": error_message,
            "error_context": error_context,
            "file_paths": [f.filename for f in self.pr_diff.files],
        }
        
        # Render template
        try:
            template = env.get_template("retry_feedback.j2")
        except TemplateNotFound as e:
            raise FileNotFoundError(
                f"Template 'retry_feedback.j2' not found in {template_dir}"
            ) from e
        return template.render(context)

    async def run_review(self) -> str:
        """Run the code review process using submit_review tool.

        Returns:
            Review result as JSON string from submit_review tool, or error
        """
        import asyncio
        from .tools import reset_submitted_review, get_submitted_review
        
        # Create retry callback
        retry_callback = RateLimitRetryCallback(max_retries=10, base_delay=1.0)
        
        while True:
            try:
                # Reset any previous submission
                reset_submitted_review()
                
                # Create initial message and invoke agent
                initial_message = self._create_initial_message()
                result = await self.agent_executor.ainvoke({"input": initial_message})
                
                # Debug: print what the agent's final output was (if verbose)
                if self.config.verbose:
                    agent_output = result.get('output', 'No output')
                    print(f"🔍 AGENT FINAL OUTPUT: {agent_output[:500]}")  # First 500 chars
                
                # Check if submit_review() was called successfully
                submitted = get_submitted_review()
                if submitted:
                    # Success! Convert back to JSON string for compatibility
                    return submitted.model_dump_json()
                else:
                    # Agent didn't call submit_review() - this shouldn't happen
                    print("⚠️ WARNING: Agent completed without calling submit_review() tool!")
                    return '{"error": "Agent did not submit review using submit_review() tool"}'
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if this is a rate limit error
                # Priority 1: Check actual status code attribute (if available)
                # Priority 2: Check error message strings
                status_code = getattr(e, 'status_code', None)
                is_rate_limit = (
                    status_code == 429
                    or "rate limit" in error_msg.lower()
                    or "too many requests" in error_msg.lower()
                    or "429" in error_msg
                )
                
                if is_rate_limit:
                    retry_callback.last_error = e
                    
                    if retry_callback.should_retry():
                        wait_time = retry_callback.get_wait_time()
                        retry_callback.increment_retry()
                        
                        print(
                            f"⏳ Rate limit hit (attempt {retry_callback.retry_count}/{retry_callback.max_retries}). "
                            f"Waiting {wait_time:.1f}s before retry...",
                            flush=True
                        )
                        await asyncio.sleep(wait_time)
                        continue  # Retry the request
                    else:
                        print(
                            f"❌ Rate limit exceeded after {retry_callback.max_retries} retries",
                            flush=True
                        )
                
                # Non-retryable error or max retries exceeded
                error_response = f'{{"error": "Review failed: {error_msg}"}}'
                print(f"❌ LLM ERROR: {error_msg}")
                return error_response

    def run_review_sync(self) -> str:
        """Run the code review process synchronously using submit_review tool.

        Returns:
            Review result as JSON string from submit_review tool, or error
        """
        from .tools import reset_submitted_review, get_submitted_review
        
        # Create retry callback
        retry_callback = RateLimitRetryCallback(max_retries=10, base_delay=1.0)
        
        while True:
            try:
                # Reset any previous submission
                reset_submitted_review()
                
                # Create initial message and invoke agent
                initial_message = self._create_initial_message()
                result = self.agent_executor.invoke({"input": initial_message})
                
                # Debug: print what the agent's final output was (if verbose)
                if self.config.verbose:
                    agent_output = result.get('output', 'No output')
                    print(f"🔍 AGENT FINAL OUTPUT: {agent_output[:500]}")  # First 500 chars
                
                # Check if submit_review() was called successfully
                submitted = get_submitted_review()
                if submitted:
                    # Success! Convert back to JSON string for compatibility
                    return submitted.model_dump_json()
                else:
                    # Agent didn't call submit_review() - this shouldn't happen
                    print("⚠️ WARNING: Agent completed without calling submit_review() tool!")
                    return '{"error": "Agent did not submit review using submit_review() tool"}'
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if this is a rate limit error
                # Priority 1: Check actual status code attribute (if available)
                # Priority 2: Check error message strings
                status_code = getattr(e, 'status_code', None)
                is_rate_limit = (
                    status_code == 429
                    or "rate limit" in error_msg.lower()
                    or "too many requests" in error_msg.lower()
                    or "429" in error_msg
                )
                
                if is_rate_limit:
                    retry_callback.last_error = e
                    
                    if retry_callback.should_retry():
                        wait_time = retry_callback.get_wait_time()
                        retry_callback.increment_retry()
                        
                        print(
                            f"⏳ Rate limit hit (attempt {retry_callback.retry_count}/{retry_callback.max_retries}). "
                            f"Waiting {wait_time:.1f}s before retry...",
                            flush=True
                        )
                        time.sleep(wait_time)
                        continue  # Retry the request
                    else:
                        print(
                            f"❌ Rate limit exceeded after {retry_callback.max_retries} retries",
                            flush=True
                        )
                
                # Non-retryable error or max retries exceeded
                error_response = f'{{"error": "Review failed: {error_msg}"}}'
                print(f"❌ LLM ERROR: {error_msg}")
                return error_response


def create_code_review_agent(
    llm: BaseLanguageModel,
    config: ReviewConfig,
    pr_diff: PullRequestDiff,
    previous_comments: list = None,
) -> CodeReviewAgent:
    """Create a code review agent instance.

    Args:
        llm: Configured language model
        config: Review configuration
        pr_diff: Pull request diff information
        previous_comments: List of previous bot comments on this PR

    Returns:
        Configured code review agent
    """
    return CodeReviewAgent(llm, config, pr_diff, previous_comments)
