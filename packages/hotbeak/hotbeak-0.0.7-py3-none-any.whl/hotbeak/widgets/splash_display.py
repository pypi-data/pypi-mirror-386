"""Splash screen display widget"""

from textual.widgets import Static


class SplashDisplay(Static):
    """Widget to display ASCII art splash screens"""

    def __init__(self, splash_content: str, **kwargs) -> None:
        """Initialize with splash screen content

        Args:
            splash_content: The ASCII art content to display
        """
        super().__init__(**kwargs)
        self.splash_content = splash_content

    def render(self) -> str:
        """Render the splash content"""
        return self.splash_content
