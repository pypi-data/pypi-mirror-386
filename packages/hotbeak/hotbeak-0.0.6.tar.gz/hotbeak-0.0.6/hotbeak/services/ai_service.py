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
        Stream AI response with support for human-in-the-loop interrupts.
        Uses dual-mode streaming (updates and messages) to detect interrupts.

        Args:
            user_message: The message from the user

        Yields:
            Dict with type and data for each content block or interrupt:
            - {"type": "text", "text": "..."}
            - {"type": "reasoning", "reasoning": "..."}
            - {"type": "tool_call_chunk", "name": "...", "args": "...", "id": "..."}
            - {"type": "tool_result", "content": "..."}
            - {"type": "interrupt", "action_requests": [...], "review_configs": [...]}
        """
        async for stream_mode, data in self.agent.astream(
            {"messages": [{"role": "user", "content": user_message}]},
            config={"configurable": {"thread_id": self.thread_id}},
            stream_mode=["messages", "updates"],
        ):
            # Check for interrupts in updates stream
            if stream_mode == "updates" and isinstance(data, dict) and "__interrupt__" in data:
                # Extract interrupt information
                interrupts = data["__interrupt__"][0].value
                yield {
                    "type": "interrupt",
                    "action_requests": interrupts["action_requests"],
                    "review_configs": interrupts["review_configs"],
                }
                # Stop streaming when we hit an interrupt - wait for user decision
                return

            # Process messages stream (same as stream_response)
            elif stream_mode == "messages":
                # data is a tuple: (message, metadata)
                message, metadata = data

                # Handle AIMessageChunk - process content blocks
                if isinstance(message, AIMessageChunk):
                    for block in message.content_blocks:
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
                elif isinstance(message, ToolMessage):
                    # Extract text content from ToolMessage
                    if message.content:
                        yield {
                            "type": "tool_result",
                            "content": message.content,
                            "tool_call_id": message.tool_call_id,
                        }

    async def respond_to_interrupt(self, decisions: list[dict]):
        """
        Resume agent execution after interrupt with user decisions.

        Args:
            decisions: List of decision dicts, one per action_request, in order
                      Each dict should have {"type": "approve"} or {"type": "reject"}

        Yields:
            Same format as stream_response_with_interrupts
        """
        from langgraph.types import Command

        # Resume execution with decisions
        async for stream_mode, data in self.agent.astream(
            Command(resume={"decisions": decisions}),
            config={"configurable": {"thread_id": self.thread_id}},
            stream_mode=["messages", "updates"],
        ):
            # Check for interrupts in updates stream (there could be multiple interrupts)
            if stream_mode == "updates" and isinstance(data, dict) and "__interrupt__" in data:
                # Extract interrupt information
                interrupts = data["__interrupt__"][0].value
                yield {
                    "type": "interrupt",
                    "action_requests": interrupts["action_requests"],
                    "review_configs": interrupts["review_configs"],
                }
                # Stop streaming when we hit another interrupt
                return

            # Process messages stream
            elif stream_mode == "messages":
                # data is a tuple: (message, metadata)
                message, metadata = data

                # Handle AIMessageChunk - process content blocks
                if isinstance(message, AIMessageChunk):
                    for block in message.content_blocks:
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
                elif isinstance(message, ToolMessage):
                    # Extract text content from ToolMessage
                    if message.content:
                        yield {
                            "type": "tool_result",
                            "content": message.content,
                            "tool_call_id": message.tool_call_id,
                        }
