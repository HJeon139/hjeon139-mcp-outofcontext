"""Performance-oriented tests with lightweight scale to validate fast paths."""

from __future__ import annotations

import os
import time
from datetime import datetime

import pytest

from hjeon139_mcp_outofcontext.models import ContextSegment
from hjeon139_mcp_outofcontext.tokenizer import Tokenizer

RUN_PERFORMANCE = bool(os.getenv("RUN_PERFORMANCE_TESTS"))


@pytest.mark.performance
@pytest.mark.skipif(not RUN_PERFORMANCE, reason="Set RUN_PERFORMANCE_TESTS=1 to run")
def test_tokenizer_cache_reuse(sample_segments: list[ContextSegment]) -> None:
    """Ensure cached token counts are reused without recomputation."""
    segment = sample_segments[0].model_copy()
    tokenizer = Tokenizer(model="gpt-4")

    first_count = tokenizer.count_segment_tokens(segment)
    first_computed_at = segment.tokens_computed_at

    second_count = tokenizer.count_segment_tokens(segment)
    second_computed_at = segment.tokens_computed_at

    assert first_count == second_count
    assert second_computed_at == first_computed_at


@pytest.mark.performance
@pytest.mark.skipif(not RUN_PERFORMANCE, reason="Set RUN_PERFORMANCE_TESTS=1 to run")
def test_keyword_search_remains_fast(app_state, project_id: str) -> None:
    """Validate inverted index search stays sub-second for hundreds of segments."""
    start_time = time.perf_counter()
    for idx in range(300):
        timestamp = datetime.now()
        segment = ContextSegment(
            segment_id=f"perf-{idx}",
            text=f"searchable text {idx}",
            type="message",
            project_id=project_id,
            task_id=None,
            created_at=timestamp,
            last_touched_at=timestamp,
            pinned=False,
            generation="young",
            gc_survival_count=0,
            refcount=0,
            file_path=None,
            line_range=None,
            tags=["perf"],
            topic_id=None,
            tokens=None,
            tokens_computed_at=None,
            text_hash=None,
            tier="working",
        )
        app_state.storage.store_segment(segment, project_id)
        app_state.storage.stash_segment(segment, project_id)

    results = app_state.storage.search_stashed("searchable", {}, project_id)
    duration = time.perf_counter() - start_time

    assert len(results) == 300
    assert duration < 0.5
