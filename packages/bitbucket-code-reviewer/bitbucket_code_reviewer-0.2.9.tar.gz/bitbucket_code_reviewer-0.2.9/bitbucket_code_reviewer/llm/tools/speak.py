"""Tool for LLM to communicate status updates to the user."""

from langchain_core.tools import tool

from ..callbacks import LLMTimingCallback


@tool
def speak(message: str) -> str:
    """Communicate status updates or information to the user.
    
    Use this tool to inform the user about:
    - Progress updates (e.g., "Completed reading all files, preparing review")
    - Important findings or observations
    - Next steps you're about to take
    - Anything else the user might want to know during the review process
    
    This is especially useful before time-consuming operations like building
    the final review summary.
    
    Args:
        message: The message to communicate to the user
        
    Returns:
        Confirmation that the message was displayed
    """
    timing = LLMTimingCallback.get_and_clear_timing()
    output = f"💬 {message}"
    if timing:
        output += f" {timing}"
    print(output, flush=True)
    return "Message displayed to user"

