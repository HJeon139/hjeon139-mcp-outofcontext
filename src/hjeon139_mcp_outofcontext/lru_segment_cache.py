"""LRU cache for active segments with disk eviction."""

from collections import OrderedDict
from typing import TYPE_CHECKING

from .models import ContextSegment

if TYPE_CHECKING:
    from .storage import StorageLayer


class LRUSegmentCache:
    """LRU cache for active segments with disk eviction."""

    def __init__(self, maxsize: int = 10000, storage: "StorageLayer | None" = None) -> None:
        """Initialize LRU cache.

        Args:
            maxsize: Maximum number of segments to keep in memory
            storage: Storage layer instance for disk eviction
        """
        self.maxsize = maxsize
        self.storage = storage
        self.cache: OrderedDict[str, ContextSegment] = OrderedDict()
        self.evicted_to_disk: set[str] = set()  # Track evicted segments

    def get(self, segment_id: str) -> ContextSegment | None:
        """Get segment, loading from disk if evicted.

        Args:
            segment_id: Segment identifier

        Returns:
            ContextSegment if found, None otherwise
        """
        if segment_id in self.cache:
            # Move to end (most recently used)
            segment = self.cache.pop(segment_id)
            self.cache[segment_id] = segment
            return segment

        # Check if evicted to disk
        if segment_id in self.evicted_to_disk and self.storage:
            # Load from disk
            loaded_segment = self.storage._load_evicted_segment(segment_id)
            if loaded_segment:
                self.put(segment_id, loaded_segment)
                return loaded_segment

        return None

    def put(self, segment_id: str, segment: ContextSegment) -> None:
        """Add segment, evicting LRU if needed.

        Args:
            segment_id: Segment identifier
            segment: Context segment to cache
        """
        if segment_id in self.cache:
            # Update existing
            self.cache.move_to_end(segment_id)
            self.cache[segment_id] = segment
            return

        # Add new segment
        if len(self.cache) >= self.maxsize:
            # Evict LRU
            evicted_id, evicted_segment = self.cache.popitem(last=False)
            self._evict_to_disk(evicted_id, evicted_segment)

        self.cache[segment_id] = segment
        self.evicted_to_disk.discard(segment_id)

    def _evict_to_disk(self, segment_id: str, segment: ContextSegment) -> None:
        """Evict segment to disk storage.

        Args:
            segment_id: Segment identifier
            segment: Segment to evict
        """
        if self.storage:
            self.storage._save_evicted_segment(segment_id, segment)
            self.evicted_to_disk.add(segment_id)

    def remove(self, segment_id: str) -> None:
        """Remove segment from cache.

        Args:
            segment_id: Segment identifier to remove
        """
        self.cache.pop(segment_id, None)
        self.evicted_to_disk.discard(segment_id)

    def clear(self) -> None:
        """Clear all segments from cache."""
        self.cache.clear()
        self.evicted_to_disk.clear()
