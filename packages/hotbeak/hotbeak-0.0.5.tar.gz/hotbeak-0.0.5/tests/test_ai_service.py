"""Tests for AIService - business logic tests (no UI dependency)"""

import pytest

from hotbeak.services.ai_service import AIService


@pytest.mark.asyncio
async def test_get_response_parrots_message():
    """Test that AIService parrots back the user message"""
    service = AIService()
    response = await service.get_response("Hello, world!")

    assert "Hello, world!" in response
    assert response.startswith("You said:")


@pytest.mark.asyncio
async def test_get_response_handles_empty_string():
    """Test that AIService handles empty messages"""
    service = AIService()
    response = await service.get_response("")

    assert response == "You said: "
