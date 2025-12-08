"""Tokenizer for counting tokens using tiktoken."""

import hashlib
from datetime import datetime
from typing import TYPE_CHECKING

import tiktoken

from .models import ContextSegment

if TYPE_CHECKING:
    pass


class Tokenizer:
    """Tokenizer wrapper around tiktoken for token counting with caching."""

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

    def _compute_text_hash(self, text: str) -> str:
        """Compute hash of text for cache invalidation.

        Args:
            text: Text to hash

        Returns:
            Hex digest of text hash
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _text_changed(self, segment: ContextSegment) -> bool:
        """Check if segment text has changed since last count.

        Args:
            segment: Context segment to check

        Returns:
            True if text has changed, False otherwise
        """
        if segment.text_hash is None:
            return True
        current_hash = self._compute_text_hash(segment.text)
        return current_hash != segment.text_hash

    def count_segment_tokens(self, segment: ContextSegment, force_recompute: bool = False) -> int:
        """Count tokens for a segment, using cached value if available.

        Args:
            segment: Context segment to count tokens for
            force_recompute: Force recomputation even if cache exists

        Returns:
            Number of tokens (uses cached value if available, otherwise computes)
        """
        # Force recompute if requested
        if force_recompute:
            count = self.count_tokens(segment.text)
            segment.tokens = count
            segment.tokens_computed_at = datetime.now()
            segment.text_hash = self._compute_text_hash(segment.text)
            return count

        # If tokens is set and text_hash matches, use cached value
        if (
            segment.tokens is not None
            and segment.text_hash is not None
            and not self._text_changed(segment)
        ):
            return segment.tokens

        # If tokens is set but text_hash is None, trust the tokens and set hash
        if segment.tokens is not None and segment.text_hash is None:
            segment.text_hash = self._compute_text_hash(segment.text)
            return segment.tokens

        # Compute and cache
        count = self.count_tokens(segment.text)
        segment.tokens = count
        segment.tokens_computed_at = datetime.now()
        segment.text_hash = self._compute_text_hash(segment.text)
        return count
