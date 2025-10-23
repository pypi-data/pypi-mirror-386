"""MessageList widget - displays chat messages"""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

from hotbeak.widgets.splash_display import SplashDisplay


class Message(Static):
    """Individual message widget"""

    content_blocks = reactive([], layout=True)

    def __init__(self, role: str, content: str = "") -> None:
        super().__init__()
        self.role = role
        if content:
            self.content_blocks = [{"type": "text", "text": content}]
        self.add_class(f"message-{role}")

    def render(self) -> str:
        """Render message content with support for different block types"""
        prefix = "You: " if self.role == "user" else "AI: "

        parts = []
        for block in self.content_blocks:
            block_type = block.get("type")

            if block_type == "text":
                parts.append(block.get("text", ""))
            elif block_type == "reasoning":
                reasoning = block.get("reasoning", "")
                if reasoning:
                    parts.append(
                        f"\n[dim italic]💭 Thinking: {reasoning}[/dim italic]\n"
                    )
            elif block_type == "tool_call":
                name = block.get("name", "unknown")
                args = block.get("args", {})
                parts.append(f"\n[cyan]🔧 Using tool: {name}({args})[/cyan]\n")
            elif block_type == "tool_result":
                content = block.get("content", "")
                parts.append(f"\n[green]✓ Tool result: {content}[/green]\n")

        return f"{prefix}{''.join(parts)}"

    def append_content_block(self, block: dict) -> None:
        """Append a content block to the message (for streaming)"""
        block_type = block.get("type")

        # Merge consecutive text blocks
        if (
            self.content_blocks
            and self.content_blocks[-1].get("type") == "text"
            and block_type == "text"
        ):
            self.content_blocks[-1]["text"] += block.get("text", "")
            # Trigger reactive update
            self.mutate_reactive(Message.content_blocks)

        # Accumulate tool_call_chunk into a complete tool_call
        elif block_type == "tool_call_chunk":
            # Find existing tool_call with same id or create new one
            tool_call_id = block.get("id")
            tool_call_index = block.get("index")

            # Try to find existing tool call block
            existing_block = None
            for b in self.content_blocks:
                if b.get("type") == "tool_call" and (
                    b.get("id") == tool_call_id or b.get("index") == tool_call_index
                ):
                    existing_block = b
                    break

            if existing_block:
                # Update existing tool call
                if block.get("name"):
                    existing_block["name"] = block.get("name")
                if block.get("id"):
                    existing_block["id"] = block.get("id")
                # Accumulate args (they come as incremental JSON strings)
                existing_block["args"] += block.get("args", "")
                # Trigger reactive update
                self.mutate_reactive(Message.content_blocks)
            else:
                # Create new tool call block
                self.content_blocks = self.content_blocks + [
                    {
                        "type": "tool_call",
                        "name": block.get("name", ""),
                        "args": block.get("args", ""),
                        "id": block.get("id"),
                        "index": block.get("index"),
                    }
                ]

        else:
            # Add new block for other types
            self.content_blocks = self.content_blocks + [block]


class MessageList(VerticalScroll):
    """Widget for displaying list of messages - self-contained rendering"""

    message_count = reactive(0)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.can_focus = False

    def compose(self) -> ComposeResult:
        """Initial empty state with ASCII art splash"""
        # Load smoke ASCII art
        splash_path = Path(__file__).parent.parent / "splash" / "smoke.txt"
        try:
            splash_content = splash_path.read_text()
        except FileNotFoundError:
            splash_content = "Start chatting by typing a message below!"

        yield SplashDisplay(splash_content, id="welcome-message")

    async def add_message(self, role: str, content: str) -> Message:
        """Add a new message to the list and return it"""
        # Remove welcome message on first message
        if self.message_count == 0:
            welcome = self.query_one("#welcome-message", SplashDisplay)
            await welcome.remove()

        # Create and mount new message
        message = Message(role, content)
        await self.mount(message)

        # Scroll to bottom
        self.scroll_end(animate=False)

        # Update count
        self.message_count += 1

        return message
