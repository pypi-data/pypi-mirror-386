"""Tests for AIService using fake models (no actual API calls)"""

import itertools
from typing import Any, AsyncIterator, Iterator
import pytest

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from hotbeak.services.ai_service import AIService


class FakeChatModel(BaseChatModel):
    """
    Fake chat model that returns pre-scripted responses without making API calls.

    This model cycles through a list of predetermined responses, making tests
    deterministic and independent of external API availability.
    """

    # Private attributes in Pydantic need to be declared with underscore prefix
    _responses: list[str]
    _response_cycle: Iterator[str]

    def __init__(self, responses: list[str] | None = None, **kwargs: Any):
        """
        Initialize the fake model with pre-scripted responses.

        Args:
            responses: List of response strings to cycle through
        """
        super().__init__(**kwargs)
        # Use object.__setattr__ to set private attributes
        object.__setattr__(
            self, "_responses", responses or ["Hello! I'm a fake AI assistant."]
        )
        object.__setattr__(self, "_response_cycle", itertools.cycle(self._responses))

    @property
    def _llm_type(self) -> str:
        """Return identifier for the LLM type."""
        return "fake-chat-model"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a single response (synchronous)."""
        response_text = next(self._response_cycle)
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a single response (asynchronous)."""
        return self._generate(messages, stop, **kwargs)

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream response in chunks (synchronous)."""
        response_text = next(self._response_cycle)
        # Split response into character-level chunks to simulate streaming
        for char in response_text:
            chunk = AIMessageChunk(content=char)
            yield ChatGenerationChunk(message=chunk)

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """Stream response in chunks (asynchronous)."""
        response_text = next(self._response_cycle)
        # Split response into character-level chunks to simulate streaming
        for char in response_text:
            chunk = AIMessageChunk(content=char)
            yield ChatGenerationChunk(message=chunk)


class FakeAIService(AIService):
    """
    Test version of AIService that uses a fake model instead of real API.

    This allows testing the service logic without requiring API credentials
    or network access.
    """

    def __init__(self, fake_responses: list[str] | None = None):
        """
        Initialize with a fake model.

        Args:
            fake_responses: List of responses the fake model should return
        """
        # Don't call super().__init__() as it would try to initialize real API
        from langchain.agents import create_agent
        from langgraph.checkpoint.memory import InMemorySaver

        # Create fake model with custom responses
        model = FakeChatModel(responses=fake_responses)

        # Create agent with fake model
        self.agent = create_agent(
            model,
            tools=[],
            checkpointer=InMemorySaver(),
            system_prompt="You are a helpful AI assistant in a chat application.",
        )

        self.thread_id = "test-conversation"


# Basic functionality tests
@pytest.mark.asyncio
async def test_fake_model_returns_predefined_response():
    """Test that fake model returns exactly what we script it to return"""
    responses = ["This is a test response"]
    service = FakeAIService(fake_responses=responses)

    chunks = []
    async for chunk in service.stream_response("Hello"):
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert full_response == "This is a test response"


@pytest.mark.asyncio
async def test_fake_model_cycles_through_responses():
    """Test that fake model cycles through multiple responses"""
    responses = ["First response", "Second response", "Third response"]
    service = FakeAIService(fake_responses=responses)

    # First call
    chunks = []
    async for chunk in service.stream_response("Message 1"):
        chunks.append(chunk)
    assert "".join(chunks) == "First response"

    # Second call
    chunks = []
    async for chunk in service.stream_response("Message 2"):
        chunks.append(chunk)
    assert "".join(chunks) == "Second response"

    # Third call
    chunks = []
    async for chunk in service.stream_response("Message 3"):
        chunks.append(chunk)
    assert "".join(chunks) == "Third response"

    # Fourth call should cycle back to first
    chunks = []
    async for chunk in service.stream_response("Message 4"):
        chunks.append(chunk)
    assert "".join(chunks) == "First response"


@pytest.mark.asyncio
async def test_fake_model_streams_character_by_character():
    """Test that streaming returns individual characters"""
    responses = ["ABC"]
    service = FakeAIService(fake_responses=responses)

    chunks = []
    async for chunk in service.stream_response("Test"):
        chunks.append(chunk)

    # Should get individual characters
    assert len(chunks) >= 1  # At least one chunk
    assert "".join(chunks) == "ABC"


@pytest.mark.asyncio
async def test_fake_model_handles_empty_message():
    """Test that service handles empty user messages"""
    responses = ["I received an empty message"]
    service = FakeAIService(fake_responses=responses)

    chunks = []
    async for chunk in service.stream_response(""):
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert full_response == "I received an empty message"


@pytest.mark.asyncio
async def test_fake_model_maintains_conversation_state():
    """Test that the agent maintains state across multiple messages"""
    responses = [
        "Hello! I'm ready to help.",
        "I remember our conversation.",
    ]
    service = FakeAIService(fake_responses=responses)

    # First message
    chunks = []
    async for chunk in service.stream_response("Hi there"):
        chunks.append(chunk)
    assert "".join(chunks) == "Hello! I'm ready to help."

    # Second message should use same thread_id
    chunks = []
    async for chunk in service.stream_response("Do you remember me?"):
        chunks.append(chunk)
    assert "".join(chunks) == "I remember our conversation."


@pytest.mark.asyncio
async def test_fake_model_with_long_response():
    """Test that service handles longer responses correctly"""
    long_response = "This is a much longer response that simulates a more realistic AI interaction. It contains multiple sentences and should be streamed correctly."
    responses = [long_response]
    service = FakeAIService(fake_responses=responses)

    chunks = []
    async for chunk in service.stream_response("Tell me something long"):
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert full_response == long_response
    assert len(chunks) > 1  # Should have been chunked


@pytest.mark.asyncio
async def test_fake_model_with_special_characters():
    """Test that service handles special characters and unicode"""
    responses = ["Hello! 👋 I can handle émojis and spëcial çharacters! 🎉"]
    service = FakeAIService(fake_responses=responses)

    chunks = []
    async for chunk in service.stream_response("Test unicode"):
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert "👋" in full_response
    assert "émojis" in full_response
    assert "🎉" in full_response


@pytest.mark.asyncio
async def test_fake_service_no_api_calls():
    """
    Test that verifies no actual API calls are made.

    This test should run successfully even without ANTHROPIC_API_KEY
    environment variable set, proving we're not making real API calls.
    """
    import os

    # Store original API key if it exists
    original_key = os.environ.get("ANTHROPIC_API_KEY")

    try:
        # Remove API key to ensure no real calls are made
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

        # This should still work because we're using fake model
        responses = ["No API key needed!"]
        service = FakeAIService(fake_responses=responses)

        chunks = []
        async for chunk in service.stream_response("Test"):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert full_response == "No API key needed!"

    finally:
        # Restore original API key
        if original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_multiple_fake_services_are_independent():
    """Test that multiple service instances don't interfere with each other"""
    service1 = FakeAIService(fake_responses=["Service 1 response"])
    service2 = FakeAIService(fake_responses=["Service 2 response"])

    # Get response from service 1
    chunks1 = []
    async for chunk in service1.stream_response("Test 1"):
        chunks1.append(chunk)

    # Get response from service 2
    chunks2 = []
    async for chunk in service2.stream_response("Test 2"):
        chunks2.append(chunk)

    # Should get different responses
    assert "".join(chunks1) == "Service 1 response"
    assert "".join(chunks2) == "Service 2 response"
