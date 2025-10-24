"""Tests for ChatApp"""

import pytest
from hotbeak.app import ChatApp


@pytest.mark.asyncio
async def test_app_runs():
    """Test that the app can be instantiated and run in test mode"""
    app = ChatApp()
    async with app.run_test() as pilot:
        assert app.is_running
        assert pilot is not None


@pytest.mark.asyncio
async def test_app_has_chat_input():
    """Test that the app has a chat input widget"""
    app = ChatApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        chat_input = app.screen.query_one("#chat-input")
        assert chat_input is not None


@pytest.mark.asyncio
async def test_app_has_message_list():
    """Test that the app has a message list widget"""
    app = ChatApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        message_list = app.screen.query_one("#message-list")
        assert message_list is not None
