"""Chat screen - layout and coordination of chat widgets"""

import os
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Header, Footer

from ..widgets.message_list import MessageList
from ..widgets.chat_input import ChatInput, MessageSubmitted, FileSearchRequested
from ..widgets.approval_input import ApprovalInput, InterruptDecision
from ..widgets.file_search_dropdown import FileSearchDropdown
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
        # Track pending interrupt data for when user responds
        self.pending_interrupt = None
        self.current_ai_message = None
        # Track file search state
        self._file_search_at_position = -1

    def compose(self) -> ComposeResult:
        """Layout structure for chat interface"""
        yield Header()
        with Container(id="chat-container"):
            with Vertical(id="chat-content"):
                yield MessageList(id="message-list")
                yield FileSearchDropdown(id="file-search-dropdown")
                yield ChatInput(id="chat-input")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize screen"""
        # Focus the input after mounting
        self.query_one("#chat-input", ChatInput).focus()

    async def on_key(self, event: Key) -> None:
        """Handle key events for file search navigation"""
        try:
            dropdown = self.query_one("#file-search-dropdown", FileSearchDropdown)
        except:
            return

        if not dropdown.is_visible():
            return

        # Handle arrow keys and Enter when dropdown is visible
        if event.key == "down":
            dropdown.move_selection(1)
            event.prevent_default()
            event.stop()
        elif event.key == "up":
            dropdown.move_selection(-1)
            event.prevent_default()
            event.stop()
        elif event.key == "enter":
            dropdown.select_current()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            dropdown.hide()
            self._file_search_at_position = -1
            event.prevent_default()
            event.stop()

    async def on_file_search_requested(self, event: FileSearchRequested) -> None:
        """Handle file search request from ChatInput"""
        dropdown = self.query_one("#file-search-dropdown", FileSearchDropdown)

        if event.at_position == -1:
            # Hide dropdown only if @ was removed
            dropdown.hide()
            self._file_search_at_position = -1
            return

        # Store the @ position
        self._file_search_at_position = event.at_position

        # Search for files (empty query shows all files)
        files = self._search_files(event.query)
        dropdown.show_results(files)

    def _search_files(self, query: str, max_results: int = 10) -> list[str]:
        """Search for files matching the query in the current directory."""
        try:
            cwd = Path.cwd()
            matches = []

            # Walk through the directory tree
            for root, dirs, files in os.walk(cwd):
                # Skip hidden directories and common ignore patterns
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["node_modules", "__pycache__", "venv", ".git"]
                ]

                for filename in files:
                    # Skip hidden files
                    if filename.startswith("."):
                        continue

                    # Check if filename matches query (case-insensitive)
                    # If query is empty, show all files
                    if not query or query.lower() in filename.lower():
                        file_path = Path(root) / filename
                        # Get relative path from cwd
                        try:
                            rel_path = file_path.relative_to(cwd)
                            matches.append(str(rel_path))
                        except ValueError:
                            # If not relative to cwd, use absolute path
                            matches.append(str(file_path))

                        if len(matches) >= max_results:
                            return matches

            return matches
        except Exception as e:
            self.app.notify(f"Error searching files: {e}", severity="error")
            return []

    async def on_file_search_dropdown_file_selected(
        self, event: FileSearchDropdown.FileSelected
    ) -> None:
        """Handle file selection from dropdown"""
        chat_input = self.query_one("#chat-input", ChatInput)
        dropdown = self.query_one("#file-search-dropdown", FileSearchDropdown)

        # Insert the selected file path
        chat_input.insert_file_path(event.file_path, self._file_search_at_position)

        # Hide the dropdown
        dropdown.hide()
        self._file_search_at_position = -1

        # Focus back on input
        chat_input.focus()

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
        try:
            # Always use interrupt-aware streaming - interrupts are detected automatically
            async for content_block in self.ai_service.stream_response(user_message):
                # Check for interrupt
                if content_block.get("type") == "interrupt":
                    # Store interrupt data and current message
                    self.pending_interrupt = content_block
                    self.current_ai_message = ai_message

                    # Replace ChatInput with ApprovalInput
                    chat_input = self.query_one("#chat-input", ChatInput)
                    chat_content = self.query_one("#chat-content", Vertical)
                    action_requests = content_block["action_requests"]

                    # For now, handle first action request (could be enhanced for multiple)
                    action_request = action_requests[0] if action_requests else {}

                    # Create approval input and mount it to parent, then remove chat input
                    approval_input = ApprovalInput(action_request, id="approval-input")
                    await chat_content.mount(approval_input)
                    await chat_input.remove()

                    # Stop streaming - wait for user decision
                    return

                # Add each content block (text, reasoning, tool_call, etc.) to the message
                ai_message.append_content_block(content_block)
                ai_message.refresh()  # Force re-render after each block
                # Auto-scroll as content arrives
                message_list.scroll_end(animate=False)
        except Exception as e:
            # Log any exceptions to help debug
            self.app.notify(f"Error in streaming: {type(e).__name__}: {e}", severity="error", timeout=10)
            import traceback
            traceback.print_exc()

    async def on_interrupt_decision(self, event: InterruptDecision) -> None:
        """Handle user decision on an interrupt"""
        if self.pending_interrupt is None:
            return

        message_list = self.query_one("#message-list", MessageList)

        # Replace ApprovalInput with ChatInput
        approval_input = self.query_one("#approval-input", ApprovalInput)
        chat_content = self.query_one("#chat-content", Vertical)
        chat_input = ChatInput(id="chat-input")
        await chat_content.mount(chat_input)
        await approval_input.remove()

        # Build decision list (one per action request)
        decisions = [
            {"type": event.decision} for _ in self.pending_interrupt["action_requests"]
        ]

        # If user rejected, add rejection message and stop
        if event.decision == "reject":
            if self.current_ai_message:
                self.current_ai_message.append_content_block(
                    {"type": "text", "text": "\n\n[Tool call rejected by user]"}
                )
                self.current_ai_message.refresh()
            self.pending_interrupt = None
            self.current_ai_message = None
            # Focus back on input
            chat_input.focus()
            return

        # Resume execution with approval
        self.run_worker(self._continue_after_interrupt(decisions, message_list, chat_input))

    async def _continue_after_interrupt(self, decisions: list[dict], message_list, chat_input: ChatInput) -> None:
        """Continue streaming after interrupt approval"""
        async for content_block in self.ai_service.respond_to_interrupt(decisions):
            # Check for another interrupt
            if content_block.get("type") == "interrupt":
                # Store new interrupt data
                self.pending_interrupt = content_block

                # Replace ChatInput with ApprovalInput again
                chat_content = self.query_one("#chat-content", Vertical)
                action_requests = content_block["action_requests"]
                action_request = action_requests[0] if action_requests else {}

                approval_input = ApprovalInput(action_request, id="approval-input")
                await chat_content.mount(approval_input)
                await chat_input.remove()

                return

            # Continue appending to the same AI message
            if self.current_ai_message:
                self.current_ai_message.append_content_block(content_block)
                self.current_ai_message.refresh()
                message_list.scroll_end(animate=False)

        # Clear pending interrupt when done and focus input
        self.pending_interrupt = None
        self.current_ai_message = None
        chat_input.focus()

    def action_quit(self) -> None:
        """Quit the application"""
        self.app.exit()
