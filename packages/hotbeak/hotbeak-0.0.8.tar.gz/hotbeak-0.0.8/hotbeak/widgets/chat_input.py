"""ChatInput widget - handles user text input"""

import os
from pathlib import Path
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input


class MessageSubmitted(Message):
    """Message posted when user submits a message"""

    def __init__(self, message: str, is_shell_command: bool = False) -> None:
        self.message = message
        self.is_shell_command = is_shell_command
        super().__init__()


class FileSearchRequested(Message):
    """Message posted when @ is detected and file search should be shown"""

    def __init__(self, query: str, at_position: int) -> None:
        self.query = query
        self.at_position = at_position
        super().__init__()


class ChatInput(Input):
    """Input widget for chat messages - self-contained input handling"""

    is_shell_command = reactive(False)

    def __init__(self, **kwargs) -> None:
        super().__init__(placeholder="Type your message and press Enter...", **kwargs)
        self._last_at_position = -1

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Check if input starts with ! to indicate shell command or @ for file search"""
        value = event.value
        new_is_shell = value.startswith("!")

        if new_is_shell != self.is_shell_command:
            self.is_shell_command = new_is_shell
            self.set_class(new_is_shell, "shell-command")

        # Check for @ symbol for file search
        cursor_pos = self.cursor_position
        self._check_file_search(value, cursor_pos)

    def _check_file_search(self, value: str, cursor_pos: int) -> None:
        """Check if we should trigger file search based on @ symbol."""
        # Find the last @ before cursor position
        at_pos = -1
        for i in range(cursor_pos - 1, -1, -1):
            if i < len(value) and value[i] == "@":
                at_pos = i
                break
            # Stop at whitespace
            if i < len(value) and value[i].isspace():
                break

        if at_pos != -1:
            # Extract query after @
            query = value[at_pos + 1 : cursor_pos]
            # Post message to parent to trigger file search
            self.post_message(FileSearchRequested(query, at_pos))
            self._last_at_position = at_pos
        elif self._last_at_position != -1:
            # @ was removed or we moved away from it
            self.post_message(FileSearchRequested("", -1))
            self._last_at_position = -1

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key - post message to parent"""
        message = event.value.strip()

        if message:
            # Check if this is a shell command
            is_shell = message.startswith("!")
            # Post message to parent screen for handling
            self.post_message(MessageSubmitted(message, is_shell_command=is_shell))

    def insert_file_path(self, file_path: str, at_position: int) -> None:
        """Insert a file path at the @ position."""
        current_value = self.value
        # Find the end of the current query after @
        cursor_pos = self.cursor_position
        end_pos = cursor_pos

        # Remove from @ to cursor and insert file path
        new_value = current_value[:at_position] + file_path + current_value[end_pos:]
        self.value = new_value
        # Move cursor to after the inserted file path
        self.cursor_position = at_position + len(file_path)
