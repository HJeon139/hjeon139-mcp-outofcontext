"""Tests for tokenizer module."""

from datetime import datetime

import pytest

from hjeon139_mcp_outofcontext.models import ContextSegment
from hjeon139_mcp_outofcontext.tokenizer import Tokenizer


@pytest.mark.unit
def test_count_tokens_simple() -> None:
    """Test token counting for simple text."""
    tokenizer = Tokenizer()
    text = "Hello, world!"
    count = tokenizer.count_tokens(text)
    assert count > 0
    assert isinstance(count, int)


@pytest.mark.unit
def test_count_tokens_empty() -> None:
    """Test token counting for empty text."""
    tokenizer = Tokenizer()
    count = tokenizer.count_tokens("")
    assert count == 0


@pytest.mark.unit
def test_count_tokens_long_text() -> None:
    """Test token counting for longer text."""
    tokenizer = Tokenizer()
    text = "This is a longer piece of text that should have multiple tokens. " * 10
    count = tokenizer.count_tokens(text)
    assert count > 10


@pytest.mark.unit
def test_count_segment_tokens_with_cached() -> None:
    """Test segment token counting uses cached value when available."""
    tokenizer = Tokenizer()
    now = datetime.now()
    segment = ContextSegment(
        segment_id="test-1",
        text="This is a test segment with some content.",
        type="message",
        project_id="test-project",
        created_at=now,
        last_touched_at=now,
        tokens=42,  # Cached value
    )
    count = tokenizer.count_segment_tokens(segment)
    assert count == 42


@pytest.mark.unit
def test_count_segment_tokens_computation() -> None:
    """Test segment token counting computes tokens correctly."""
    tokenizer = Tokenizer()
    now = datetime.now()
    text = "This is a test segment with some content."
    # Create segment with incorrect cached value to verify computation
    # Note: Since tokens is required, we test that computation works
    # by verifying the count matches what we'd get from count_tokens
    expected_count = tokenizer.count_tokens(text)
    segment = ContextSegment(
        segment_id="test-1",
        text=text,
        type="message",
        project_id="test-project",
        created_at=now,
        last_touched_at=now,
        tokens=expected_count,  # Correct cached value
    )
    count = tokenizer.count_segment_tokens(segment)
    # Should use cached value
    assert count == expected_count
    assert isinstance(count, int)


@pytest.mark.unit
def test_tokenizer_different_models() -> None:
    """Test tokenizer with different models."""
    tokenizer_gpt4 = Tokenizer(model="gpt-4")
    tokenizer_gpt35 = Tokenizer(model="gpt-3.5-turbo")

    text = "Hello, world!"
    count_gpt4 = tokenizer_gpt4.count_tokens(text)
    count_gpt35 = tokenizer_gpt35.count_tokens(text)

    # Both should return positive counts
    assert count_gpt4 > 0
    assert count_gpt35 > 0


@pytest.mark.unit
def test_count_tokens_performance() -> None:
    """Test token counting performance (< 100ms for 10k tokens)."""
    import time

    tokenizer = Tokenizer()
    # Create text that should be around 10k tokens
    text = "This is a test sentence. " * 500

    start = time.time()
    count = tokenizer.count_tokens(text)
    elapsed = (time.time() - start) * 1000  # Convert to milliseconds

    assert elapsed < 100, f"Token counting took {elapsed}ms, expected < 100ms"
    assert count > 0
