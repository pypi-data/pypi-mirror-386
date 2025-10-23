"""ChatInput widget - handles user text input"""

from textual.message import Message
from textual.widgets import Input


class MessageSubmitted(Message):
    """Message posted when user submits a message"""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()


class ChatInput(Input):
    """Input widget for chat messages - self-contained input handling"""

    def __init__(self, **kwargs) -> None:
        super().__init__(placeholder="Type your message and press Enter...", **kwargs)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key - post message to parent"""
        message = event.value.strip()

        if message:
            # Post message to parent screen for handling
            self.post_message(MessageSubmitted(message))
