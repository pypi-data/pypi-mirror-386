"""ApprovalInput widget - replaces ChatInput during HIL interrupts for approve/reject"""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Static
from rich.text import Text


class InterruptDecision(Message):
    """Message posted when user makes a decision about an interrupt"""

    def __init__(self, decision: str) -> None:
        """
        Args:
            decision: One of "approve", "reject"
        """
        self.decision = decision
        super().__init__()


class ApprovalInput(Widget):
    """Input widget shown during HIL interrupts - displays approve/reject buttons"""

    DEFAULT_CSS = """
    ApprovalInput {
        height: auto;
        background: $panel;
        border: solid $warning;
        padding: 1;
    }

    ApprovalInput .tool-info {
        color: $text;
        margin-bottom: 1;
    }

    ApprovalInput .buttons {
        height: auto;
        align: center middle;
    }

    ApprovalInput Button {
        margin: 0 1;
    }
    """

    # Enable keyboard shortcuts
    BINDINGS = [
        ("a", "approve", "Approve"),
        ("r", "reject", "Reject"),
    ]

    def __init__(self, action_request: dict, **kwargs) -> None:
        """
        Initialize the approval input.

        Args:
            action_request: Dict with 'name', 'args', and 'description'
        """
        super().__init__(**kwargs)
        self.action_request = action_request

    def compose(self) -> ComposeResult:
        """Layout for the approval input"""
        yield Static(self._format_action_info(), classes="tool-info")
        with Horizontal(classes="buttons"):
            yield Button("✓ Approve", id="approve-btn", variant="success")
            yield Button("✗ Reject", id="reject-btn", variant="error")

    def _format_action_info(self) -> Text:
        """Format the action request information for display"""
        text = Text()
        text.append("🔔 Tool Call Approval Required  ", style="bold yellow")

        name = self.action_request.get("name", "unknown")
        args = self.action_request.get("args", {})

        text.append("Tool: ", style="bold")
        text.append(f"{name}  ", style="cyan")

        text.append("Args: ", style="bold dim")
        # Format args nicely - keep it concise
        if isinstance(args, dict):
            args_str = ", ".join(f"{k}={v}" for k, v in args.items())
            text.append(f"{args_str}", style="dim")
        else:
            text.append(f"{args}", style="dim")

        return text

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "approve-btn":
            self.post_message(InterruptDecision("approve"))
        elif event.button.id == "reject-btn":
            self.post_message(InterruptDecision("reject"))

    def action_approve(self) -> None:
        """Approve via keyboard shortcut"""
        self.post_message(InterruptDecision("approve"))

    def action_reject(self) -> None:
        """Reject via keyboard shortcut"""
        self.post_message(InterruptDecision("reject"))

    async def on_mount(self) -> None:
        """Focus the approve button when mounted"""
        approve_btn = self.query_one("#approve-btn", Button)
        approve_btn.focus()
