"""Test custom agent for CLI testing"""

from deepagents import create_deep_agent
from langchain.tools import tool


@tool
def test_tool(message: str) -> str:
    """A test tool that echoes back a message.

    Args:
        message: The message to echo

    Returns:
        The echoed message with a prefix
    """
    return f"Test agent received: {message}"


# Create a test agent that can be loaded via CLI
test_agent = create_deep_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[test_tool],
    system_prompt="You are a TEST AI assistant. Always identify yourself as the TEST agent. You have access to a test_tool.",
)
