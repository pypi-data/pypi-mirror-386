"""Bitbucket API client for pull request operations."""

import base64
from typing import Any, Optional

import requests

from ..core.config import get_app_config, get_cache_manager
from ..core.models import FileChange, PullRequestDiff, PullRequestInfo


class BitbucketClient:
    """Client for interacting with Bitbucket API."""

    BASE_URL = "https://api.bitbucket.org/2.0"

    def __init__(
        self,
        workspace: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        verbose: bool = False,
    ):
        """Initialize Bitbucket client.

        Args:
            workspace: Bitbucket workspace name
            token: Bitbucket API token (App Password or Repository Access Token)
            username: Bitbucket username (required for App Password authentication)
            verbose: Enable verbose debug output
        """
        self.workspace = workspace
        self.verbose = verbose
        self.app_config = get_app_config()
        self.token = token or self.app_config.bitbucket_token
        self.username = username or self.app_config.bitbucket_auth_username
        self.cache_manager = get_cache_manager()

        if not self.token:
            raise ValueError(
                "Bitbucket API token is required. "
                "Set BITBUCKET_TOKEN environment variable."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

        # Debug ALL environment variables
        import os

        if self.verbose:
            print("🔍 ALL ENV VARS containing 'AUTH' or 'TOKEN' or 'BITBUCKET':")
            for key, value in os.environ.items():
                if "AUTH" in key or "TOKEN" in key or "BITBUCKET" in key:
                    print(f"   {key} = '***REDACTED***' ({len(value)} chars)")

        # Try to get values directly from environment
        direct_username = os.environ.get("BB_AUTH_USERNAME")
        direct_token = os.environ.get("BITBUCKET_TOKEN")

        if self.verbose:
            print(f"🔍 DIRECT: BB_AUTH_USERNAME from os.environ = '{direct_username}'")
            print(f"🔍 DIRECT: BITBUCKET_TOKEN from os.environ = '***REDACTED***'")

        # Override with direct environment values if available
        if direct_username:
            self.username = direct_username
            if self.verbose:
                print(f"✅ OVERRIDE: Using direct BB_AUTH_USERNAME = '{self.username}'")

        if direct_token:
            self.token = direct_token
            if self.verbose:
                print(f"✅ OVERRIDE: Using direct BITBUCKET_TOKEN = '***REDACTED***'")

        # Debug Pydantic config loading
        if self.verbose:
            raw_config = self.app_config
            auth_val = raw_config.bitbucket_auth_username
            print(f"🔍 Pydantic config: bitbucket_auth_username = '{auth_val}'")
            print(f"🔍 Pydantic config: bitbucket_token = '***REDACTED***'")

            print(f"🔍 Client init: self.username = '{self.username}'")
            token_status = "***" if self.token else "None"
            print(f"🔍 Client init: self.token = '{token_status}'")

        # Set up authentication based on token type
        self._setup_authentication()

    def validate_token(self) -> bool:
        """Validate that the token works for basic API access.

        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            # Test with a simple repository info call (doesn't require PR permissions)
            test_url = f"{self.BASE_URL}/repositories/{self.workspace}"
            self._make_request("GET", test_url)
            if self.verbose:
                print("✅ Token validation successful")
            return True
        except Exception as e:
            if self.verbose:
                print(f"❌ Token validation failed: {e}")
            return False

    def _setup_authentication(self) -> None:
        """Set up authentication based on token type.

        Uses Basic Auth for App Passwords (when username is provided)
        Uses Bearer Auth for Repository Access Tokens (when no username provided)
        """
        if self.verbose:
            print(f"🔐 Setting up auth - username: '{self.username}', token length: {len(self.token) if self.token else 0}")

        if self.username:
            # App Password: Use Basic Auth
            credentials = f"{self.username}:{self.token}"
            if self.verbose:
                print(f"🔐 Credentials string: {self.username}:***")
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            if self.verbose:
                print(f"🔐 Base64 encoded: ***REDACTED***")
            self.session.headers["Authorization"] = f"Basic {encoded_credentials}"
            if self.verbose:
                print("🔐 Using Basic Auth (App Password)")
                print(f"🔐 Final auth header: Basic ***REDACTED***")
        else:
            # Repository Access Token: Use Bearer Auth
            self.session.headers["Authorization"] = f"Bearer {self.token}"
            if self.verbose:
                print("🔐 Using Bearer Auth (Repository Access Token)")
                print(f"🔐 Final auth header: Bearer ***REDACTED***")

    def get_pull_request(self, repo_slug: str, pr_id: int) -> PullRequestInfo:
        """Get pull request information.

        Args:
            repo_slug: Repository slug
            pr_id: Pull request ID

        Returns:
            PullRequestInfo object
        """
        url = (
            f"{self.BASE_URL}/repositories/{self.workspace}/"
            f"{repo_slug}/pullrequests/{pr_id}"
        )
        response = self._make_request("GET", url)

        pr_data = response.json()
        
        # Get author information for @mentions
        author_data = pr_data.get("author", {})
        
        # Get account_id for @mentions (Bitbucket Cloud uses account_id)
        author_account_id = author_data.get("account_id")
        
        # Get username (prefer username without spaces, fallback to nickname, then display_name)
        author_username = (
            author_data.get("username")
            or author_data.get("nickname")
            or author_data.get("display_name", "unknown")
        )

        return PullRequestInfo(
            id=pr_data["id"],
            title=pr_data["title"],
            description=pr_data.get("description", ""),
            source_branch=pr_data["source"]["branch"]["name"],
            target_branch=pr_data["destination"]["branch"]["name"],
            author=pr_data["author"]["display_name"],
            author_username=author_username,
            author_account_id=author_account_id,
            state=pr_data["state"],
        )

    def get_pull_request_diff(self, repo_slug: str, pr_id: int) -> PullRequestDiff:
        """Get the diff for a pull request.

        Args:
            repo_slug: Repository slug
            pr_id: Pull request ID

        Returns:
            PullRequestDiff object with diff content and file changes
        """
        cache_key = f"pr_diff_{self.workspace}_{repo_slug}_{pr_id}"

        # Try to get from cache first
        cached_data = self.cache_manager.get(cache_key)
        if cached_data:
            return PullRequestDiff(**cached_data)

        # Get PR info
        pr_info = self.get_pull_request(repo_slug, pr_id)

        # Get diff content
        diff_url = (
            f"{self.BASE_URL}/repositories/{self.workspace}/"
            f"{repo_slug}/pullrequests/{pr_id}/diff"
        )
        response = self._make_request("GET", diff_url)
        # Explicitly decode as UTF-8 to handle emojis correctly
        response.encoding = 'utf-8'
        diff_content = response.text

        # Get file changes from diffstat
        diffstat_url = (
            f"{self.BASE_URL}/repositories/{self.workspace}/"
            f"{repo_slug}/pullrequests/{pr_id}/diffstat"
        )
        response = self._make_request("GET", diffstat_url)
        diffstat_data = response.json()

        files = []
        for file_data in diffstat_data.get("values", []):
            # Handle deleted files (where "new" is null)
            if file_data.get("new") is not None:
                filename = file_data["new"]["path"]
            elif file_data.get("old") is not None:
                filename = file_data["old"]["path"]
            else:
                # Skip if neither old nor new path exists
                continue

            files.append(
                FileChange(
                    filename=filename,
                    status=file_data["status"],
                    additions=file_data.get("lines_added", 0),
                    deletions=file_data.get("lines_removed", 0),
                )
            )

        result = PullRequestDiff(
            pull_request=pr_info,
            files=files,
            diff_content=diff_content,
        )

        # Cache the result
        self.cache_manager.set(cache_key, result.model_dump())

        return result

    def add_pull_request_comment(
        self,
        repo_slug: str,
        pr_id: int,
        content: str,
        file_path: Optional[str] = None,
        line: Optional[int] = None,
        from_line: Optional[int] = None,
        to_line: Optional[int] = None,
    ) -> dict[str, Any]:
        """Add a comment to a pull request.

        Args:
            repo_slug: Repository slug
            pr_id: Pull request ID
            content: Comment content
            file_path: Optional file path for inline comment
            line: Optional line number for inline comment

        Returns:
            Comment data from API
        """
        url = (
            f"{self.BASE_URL}/repositories/{self.workspace}/"
            f"{repo_slug}/pullrequests/{pr_id}/comments"
        )

        comment_data = {"content": {"raw": content}}

        # Add inline comment data if provided
        if file_path and (line is not None or to_line is not None or from_line is not None):
            inline: dict[str, Any] = {"path": file_path}
            if from_line is not None and to_line is not None:
                inline["from"] = from_line
                inline["to"] = to_line
            elif to_line is not None:
                inline["to"] = to_line
            elif line is not None:
                # ONLY use "to" - don't set "from" (Bitbucket might reject inline when from==to on pure additions)
                inline["to"] = line
            comment_data["inline"] = inline
        
        # Debug: Print the exact payload being sent
        import json as json_lib
        print(f"🐛 DEBUG: Comment payload: {json_lib.dumps(comment_data, indent=2)}")

        response = self._make_request("POST", url, json=comment_data)
        response_data = response.json()
        
        # Debug: Print response inline object
        response_inline = response_data.get("inline")
        print(f"🐛 DEBUG: Response inline: {response_inline}")
        
        return response_data

    def get_pull_request_comments(
        self, repo_slug: str, pr_id: int
    ) -> list[dict[str, Any]]:
        """Get all non-deleted comments from a pull request.

        Args:
            repo_slug: Repository slug
            pr_id: Pull request ID

        Returns:
            List of comment dictionaries (root comments only, non-deleted, all authors)
        """
        url = (
            f"{self.BASE_URL}/repositories/{self.workspace}/"
            f"{repo_slug}/pullrequests/{pr_id}/comments?pagelen=100"
        )
        
        all_comments = []
        
        # Handle pagination
        while url:
            response = self._make_request("GET", url)
            data = response.json()
            
            # Filter for root comments (no parent) by bot username
            for comment in data.get("values", []):
                # Skip deleted comments
                if comment.get("deleted", False):
                    continue
                
                # Check if it's a root comment (no parent)
                if comment.get("parent") is not None:
                    continue
                
                # Include ALL non-deleted, non-reply comments (not just bot's own)
                # This prevents the LLM from duplicating ANY existing comment,
                # whether from bot or human reviewers
                # No author filtering needed - show all comments to LLM
                
                # Extract relevant data
                user = comment.get("user", {})
                author_name = user.get("display_name") or user.get("nickname") or user.get("username") or "Unknown"
                
                comment_data = {
                    "id": comment.get("id"),
                    "author": author_name,
                    "content": comment.get("content", {}).get("raw", ""),
                    "created_date": comment.get("created_on", ""),
                }
                
                # Add inline comment info if present
                inline = comment.get("inline")
                if inline:
                    comment_data["file_path"] = inline.get("path")
                    comment_data["line"] = inline.get("to")
                
                all_comments.append(comment_data)
            
            # Check for next page
            url = data.get("next")
        
        return all_comments

    def get_repository_info(self, repo_slug: str) -> dict[str, Any]:
        """Get repository information.

        Args:
            repo_slug: Repository slug

        Returns:
            Repository data from API
        """
        url = f"{self.BASE_URL}/repositories/{self.workspace}/{repo_slug}"
        response = self._make_request("GET", url)
        return response.json()

    def _make_request(
        self,
        method: str,
        url: str,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> requests.Response:
        """Make an HTTP request to Bitbucket API.

        Args:
            method: HTTP method
            url: Request URL
            json: JSON payload
            params: Query parameters

        Returns:
            HTTP response

        Raises:
            HTTPError: If request fails
        """
        if self.verbose:
            print(f"🔍 Making {method} request to: {url}")
            print(f"📂 Repository: {self.workspace}")
            auth_header = self.session.headers.get("Authorization", "None")
            if auth_header != "None":
                auth_type = auth_header.split()[0] if len(auth_header.split()) > 0 else "Unknown"
                auth_value = auth_header.split()[1][:20] + "..." if len(auth_header.split()) > 1 else "No value"
                print(f"🔐 Auth header: {auth_type} {auth_value}")
            else:
                print("🔐 Auth header: None")

        response = self.session.request(method, url, json=json, params=params)

        if not response.ok:
            if self.verbose:
                print(f"❌ Request failed: {response.status_code}")
                print(f"❌ Response headers: {dict(response.headers)}")
                error_data = response.json() if response.content else {}
                print(f"❌ Error data: {error_data}")
            else:
                error_data = response.json() if response.content else {}
            raise requests.HTTPError(
                f"Bitbucket API error {response.status_code}: "
                f"{error_data.get('error', {}).get('message', 'Unknown error')}"
            )

        if self.verbose:
            print(f"✅ Request successful: {response.status_code}")
        return response


def create_bitbucket_client(
    workspace: str, token: Optional[str] = None, username: Optional[str] = None, verbose: bool = False
) -> BitbucketClient:
    """Create a Bitbucket client instance.

    Args:
        workspace: Bitbucket workspace
        token: Optional API token
        username: Optional username for App Password authentication
        verbose: Enable verbose debug output

    Returns:
        Configured Bitbucket client
    """
    return BitbucketClient(workspace, token, username, verbose)
