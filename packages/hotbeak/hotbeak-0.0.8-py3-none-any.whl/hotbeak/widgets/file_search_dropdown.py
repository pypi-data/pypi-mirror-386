"""File search dropdown widget for @ mentions."""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class FileSearchDropdown(Widget):
    """Dropdown widget that displays file search results."""

    DEFAULT_CSS = """
    FileSearchDropdown {
        display: none;
        width: 100%;
        max-height: 10;
        background: $surface;
        border: tall $primary;
        padding: 0;
    }

    FileSearchDropdown.visible {
        display: block;
    }

    FileSearchDropdown VerticalScroll {
        height: auto;
        max-height: 10;
    }

    FileSearchDropdown .file-item {
        padding: 0 1;
        color: $text;
        background: $surface;
    }

    FileSearchDropdown .file-item.selected {
        background: $accent;
        color: $text;
        text-style: bold;
    }

    FileSearchDropdown .file-item:hover {
        background: $accent-darken-1;
    }

    FileSearchDropdown .no-results {
        padding: 0 1;
        color: $text-muted;
        text-style: italic;
    }
    """

    files: reactive[list[str]] = reactive(list, layout=True)
    selected_index: reactive[int] = reactive(0)

    class FileSelected(Message):
        """Posted when a file is selected from the dropdown."""

        def __init__(self, file_path: str) -> None:
            self.file_path = file_path
            super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the dropdown widget."""
        with VerticalScroll():
            yield Static("", id="file-list")

    def watch_files(self, files: list[str]) -> None:
        """Update the dropdown when files change."""
        if not files:
            self.remove_class("visible")
            self.selected_index = 0
            return

        self.add_class("visible")
        self.selected_index = 0
        self._render_files()

    def watch_selected_index(self, _old: int, new: int) -> None:
        """Update the UI when selection changes."""
        if self.files:
            # Clamp the index
            self.selected_index = max(0, min(new, len(self.files) - 1))
            self._render_files()

    def _render_files(self) -> None:
        """Render the file list."""
        file_list = self.query_one("#file-list", Static)

        if not self.files:
            file_list.update("[dim]No files found[/]")
            file_list.set_class(True, "no-results")
            return

        file_list.remove_class("no-results")

        lines = []
        for idx, file_path in enumerate(self.files):
            if idx == self.selected_index:
                lines.append(f"[reverse] {file_path} [/]")
            else:
                lines.append(f"  {file_path}")

        file_list.update("\n".join(lines))

    def move_selection(self, delta: int) -> None:
        """Move the selection up or down."""
        if self.files:
            new_index = self.selected_index + delta
            self.selected_index = max(0, min(new_index, len(self.files) - 1))

    def select_current(self) -> None:
        """Select the currently highlighted file."""
        if self.files and 0 <= self.selected_index < len(self.files):
            selected_file = self.files[self.selected_index]
            self.post_message(self.FileSelected(selected_file))
            self.hide()

    def show_results(self, files: list[str]) -> None:
        """Show the dropdown with the given files."""
        self.files = files

    def hide(self) -> None:
        """Hide the dropdown."""
        self.files = []
        self.remove_class("visible")

    def is_visible(self) -> bool:
        """Check if the dropdown is currently visible."""
        return self.has_class("visible")
