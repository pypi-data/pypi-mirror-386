"""Main application - coordination only"""

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any, Optional

from textual.app import App

from .screens.chat_screen import ChatScreen
from .services.ai_service import AIService


def load_agent_from_path(agent_path: str) -> Any:
    """
    Load an agent from a module:attribute path.

    Args:
        agent_path: Path in format "module.path:attribute" (e.g., "mypackage.agents:my_agent")

    Returns:
        The loaded agent object

    Raises:
        ValueError: If the path format is invalid
        ImportError: If the module cannot be imported
        AttributeError: If the attribute doesn't exist in the module
    """
    if ":" not in agent_path:
        raise ValueError(
            f"Invalid agent path '{agent_path}'. Expected format: 'module.path:attribute'"
        )

    module_path, attribute_name = agent_path.rsplit(":", 1)

    # Add current working directory to sys.path to allow importing local modules
    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Failed to import module '{module_path}': {e}") from e

    try:
        agent = getattr(module, attribute_name)
    except AttributeError as e:
        raise AttributeError(
            f"Module '{module_path}' has no attribute '{attribute_name}'"
        ) from e

    return agent


class ChatApp(App[None]):
    """Chat application - handles screen navigation and global services"""

    CSS_PATH = "styles/styles.tcss"

    def __init__(self, agent: Optional[Any] = None) -> None:
        super().__init__()
        self.ai_service = AIService(agent=agent)

    async def on_mount(self) -> None:
        """Initialize application"""
        await self.push_screen(ChatScreen(self.ai_service))


def main() -> None:
    """Entry point for the chat application"""
    parser = argparse.ArgumentParser(
        description="Hotbeak - AI chat application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hotbeak                              # Use default agent
  hotbeak --agent mypackage.agents:my_agent  # Use custom agent
        """,
    )

    parser.add_argument(
        "--agent",
        type=str,
        help="Agent to use in format 'module.path:attribute' (e.g., 'mypackage.agents:my_agent')",
        metavar="MODULE:ATTR",
    )

    args = parser.parse_args()

    # Load agent if specified
    agent = None
    if args.agent:
        try:
            agent = load_agent_from_path(args.agent)
            print(f"Loaded agent from: {args.agent}")
        except (ValueError, ImportError, AttributeError) as e:
            parser.error(f"Failed to load agent: {e}")

    app = ChatApp(agent=agent)
    app.run()


if __name__ == "__main__":
    main()
