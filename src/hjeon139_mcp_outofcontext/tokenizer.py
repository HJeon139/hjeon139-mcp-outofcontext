"""Tokenizer for counting tokens using tiktoken."""

from typing import TYPE_CHECKING

import tiktoken

from .models import ContextSegment

if TYPE_CHECKING:
    pass


class Tokenizer:
    """Tokenizer wrapper around tiktoken for token counting."""

    def __init__(self, model: str = "gpt-4") -> None:
        """Initialize tokenizer.

        Args:
            model: Model name to use for encoding (default: "gpt-4")
        """
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def count_segment_tokens(self, segment: ContextSegment) -> int:
        """Count tokens for a segment, using cached value if available.

        Args:
            segment: Context segment to count tokens for

        Returns:
            Number of tokens (uses cached value if available, otherwise computes)
        """
        if segment.tokens is not None:
            return segment.tokens
        return self.count_tokens(segment.text)
