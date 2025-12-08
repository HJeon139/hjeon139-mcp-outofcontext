"""Inverted index for keyword search."""

import re


class InvertedIndex:
    """Inverted index for keyword search."""

    def __init__(self) -> None:
        """Initialize inverted index."""
        # word -> set of segment_ids containing that word
        self.index: dict[str, set[str]] = {}
        # segment_id -> set of words in that segment
        self.segment_words: dict[str, set[str]] = {}

    def add_segment(self, segment_id: str, text: str) -> None:
        """Add segment to index.

        Args:
            segment_id: Segment identifier
            text: Segment text content
        """
        words = self._tokenize(text)
        self.segment_words[segment_id] = words

        for word in words:
            if word not in self.index:
                self.index[word] = set()
            self.index[word].add(segment_id)

    def remove_segment(self, segment_id: str) -> None:
        """Remove segment from index.

        Args:
            segment_id: Segment identifier to remove
        """
        if segment_id not in self.segment_words:
            return

        words = self.segment_words[segment_id]
        for word in words:
            if word in self.index:
                self.index[word].discard(segment_id)
                if not self.index[word]:
                    del self.index[word]

        del self.segment_words[segment_id]

    def search(self, query: str) -> set[str]:
        """Search for segments containing query words.

        Args:
            query: Search query string

        Returns:
            Set of segment IDs matching the query (AND search)
        """
        query_words = list(self._tokenize(query))
        if not query_words:
            return set()

        # Intersection of all word sets (AND search)
        result = self.index.get(query_words[0], set()).copy()
        for word in query_words[1:]:
            result &= self.index.get(word, set())

        return result

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize text into words (lowercase, alphanumeric).

        Args:
            text: Text to tokenize

        Returns:
            Set of unique words
        """
        words = re.findall(r"\b\w+\b", text.lower())
        return set(words)
