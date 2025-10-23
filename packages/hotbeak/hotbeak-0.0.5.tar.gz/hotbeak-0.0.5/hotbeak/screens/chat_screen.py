"""Chat screen - layout and coordination of chat widgets"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer

from ..widgets.message_list import MessageList
from ..widgets.chat_input import ChatInput, MessageSubmitted
from ..services.ai_service import AIService
from ..services.shell_service import ShellService


class ChatScreen(Screen):
    """Main chat screen - handles layout and widget coordination"""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, ai_service: AIService) -> None:
        super().__init__()
        self.ai_service = ai_service
        self.shell_service = ShellService()

    def compose(self) -> ComposeResult:
        """Layout structure for chat interface"""
        yield Header()
        with Container(id="chat-container"):
            with Vertical(id="chat-content"):
                yield MessageList(id="message-list")
                yield ChatInput(id="chat-input")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize screen"""
        # Focus the input after mounting
        self.query_one("#chat-input", ChatInput).focus()

    async def on_message_submitted(self, event: MessageSubmitted) -> None:
        """Handle user message submission"""
        message_list = self.query_one("#message-list", MessageList)
        chat_input = self.query_one("#chat-input", ChatInput)

        # Clear input
        chat_input.clear()

        if event.is_shell_command:
            # Handle shell command
            await self._handle_shell_command(event.message, message_list)
        else:
            # Handle normal AI chat message
            # Add user message
            await message_list.add_message("user", event.message)

            # Add empty AI message that will be updated with streaming
            ai_message = await message_list.add_message("assistant", "")

            # Run streaming in a background task so UI can update
            self.run_worker(self._stream_response(event.message, ai_message, message_list))

    async def _handle_shell_command(self, command: str, message_list) -> None:
        """Execute shell command and display output"""
        # Remove the ! prefix
        shell_command = command[1:].strip()

        if not shell_command:
            # Empty command after !, show error
            await message_list.add_message("system", "Error: No command specified after !")
            return

        # Add command to message list
        await message_list.add_message("shell", f"$ {shell_command}")

        # Execute command
        stdout, stderr, return_code = await self.shell_service.execute_command(
            shell_command
        )

        # Format output
        output_text = ""
        if stdout:
            output_text += stdout
        if stderr:
            if output_text:
                output_text += "\n"
            output_text += f"stderr:\n{stderr}"
        if not stdout and not stderr:
            output_text = "(no output)"

        # Add output to message list
        await message_list.add_message(
            "shell_output", output_text, return_code=return_code
        )

    async def _stream_response(
        self, user_message: str, ai_message, message_list
    ) -> None:
        """Stream AI response in background"""
        async for content_block in self.ai_service.stream_response(user_message):
            # Add each content block (text, reasoning, tool_call, etc.) to the message
            ai_message.append_content_block(content_block)
            ai_message.refresh()  # Force re-render after each block
            # Auto-scroll as content arrives
            message_list.scroll_end(animate=False)

    def action_quit(self) -> None:
        """Quit the application"""
        self.app.exit()
