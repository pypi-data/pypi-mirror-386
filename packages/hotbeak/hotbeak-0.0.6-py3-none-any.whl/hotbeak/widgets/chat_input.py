"""ChatInput widget - handles user text input"""

from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input


class MessageSubmitted(Message):
    """Message posted when user submits a message"""

    def __init__(self, message: str, is_shell_command: bool = False) -> None:
        self.message = message
        self.is_shell_command = is_shell_command
        super().__init__()


class ChatInput(Input):
    """Input widget for chat messages - self-contained input handling"""

    is_shell_command = reactive(False)

    def __init__(self, **kwargs) -> None:
        super().__init__(placeholder="Type your message and press Enter...", **kwargs)

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Check if input starts with ! to indicate shell command"""
        value = event.value
        new_is_shell = value.startswith("!")

        if new_is_shell != self.is_shell_command:
            self.is_shell_command = new_is_shell
            self.set_class(new_is_shell, "shell-command")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key - post message to parent"""
        message = event.value.strip()

        if message:
            # Check if this is a shell command
            is_shell = message.startswith("!")
            # Post message to parent screen for handling
            self.post_message(MessageSubmitted(message, is_shell_command=is_shell))
