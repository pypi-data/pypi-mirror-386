"""AIService - business logic for AI interactions (testable without UI)"""

from typing import Any, Optional

from langchain_core.messages import AIMessageChunk, ToolMessage
from langchain.tools import tool
from deepagents import create_deep_agent


@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location.

    Args:
        location: The city or location to get weather for

    Returns:
        A description of the weather
    """
    # Fake implementation that returns mock weather data
    return f"The weather in {location} is sunny and 72°F (22°C) with light winds."


class AIService:
    """Service for AI chat interactions - separates business logic from UI"""

    def __init__(self, agent: Optional[Any] = None):
        """
        Initialize the AI service with a LangChain agent.

        Args:
            agent: Optional pre-configured agent to use. If None, creates default deep agent.
        """
        if agent is not None:
            # Use provided agent
            self.agent = agent
        else:
            # Create default deep agent
            # Standard agent (kept for reference, not used)
            # model = init_chat_model("anthropic:claude-sonnet-4-5")
            # standard_agent = create_agent(
            #     model,
            #     tools=[get_weather],
            #     checkpointer=InMemorySaver(),
            #     system_prompt="You are a helpful AI assistant in a chat application. You can check the weather using the get_weather tool when asked."
            # )

            # Deep agent (default) - includes planning, filesystem, and subagent capabilities
            self.agent = create_deep_agent(
                model="claude-sonnet-4-5-20250929",
                tools=[get_weather],
                system_prompt="You are a helpful AI assistant in a chat application. You can check the weather using the get_weather tool when asked.",
            )

        # Track conversation thread
        self.thread_id = "main-conversation"

    async def stream_response(self, user_message: str):
        """
        Stream AI response for user message using LangChain agent.

        Args:
            user_message: The message from the user

        Yields:
            Dict with type and data for each content block:
            - {"type": "text", "text": "..."}
            - {"type": "reasoning", "reasoning": "..."}
            - {"type": "tool_call_chunk", "name": "...", "args": "...", "id": "..."}
            - {"type": "tool_result", "content": "..."}
        """
        async for chunk, metadata in self.agent.astream(
            {"messages": [{"role": "user", "content": user_message}]},
            config={"configurable": {"thread_id": self.thread_id}},
            stream_mode="messages",
        ):
            # Handle AIMessageChunk - process content blocks
            if isinstance(chunk, AIMessageChunk):
                for block in chunk.content_blocks:
                    block_type = block.get("type")

                    if block_type == "text":
                        text = block.get("text", "")
                        if text:  # Only yield non-empty text
                            yield {"type": "text", "text": text}

                    elif block_type == "reasoning":
                        reasoning = block.get("reasoning", "")
                        if reasoning:
                            yield {"type": "reasoning", "reasoning": reasoning}

                    elif block_type == "tool_call_chunk":
                        # Yield tool call chunks as they arrive (for incremental display)
                        yield {
                            "type": "tool_call_chunk",
                            "name": block.get("name"),
                            "args": block.get("args", ""),
                            "id": block.get("id"),
                            "index": block.get("index"),
                        }

            # Handle ToolMessage - contains tool execution results
            elif isinstance(chunk, ToolMessage):
                # Extract text content from ToolMessage
                if chunk.content:
                    yield {
                        "type": "tool_result",
                        "content": chunk.content,
                        "tool_call_id": chunk.tool_call_id,
                    }
