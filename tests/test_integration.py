"""Integration tests covering end-to-end context workflows."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from hjeon139_mcp_outofcontext.models import ContextSegment


@pytest.mark.integration
def test_context_workflow_analyze_stash_retrieve(
    app_state,
    context_descriptors,
    project_id: str,
) -> None:
    """End-to-end coverage: analyze context, stash, and retrieve segments."""
    result = app_state.context_manager.analyze_context(context_descriptors, project_id)
    assert result.total_tokens >= 0
    working_set = app_state.context_manager.get_working_set(project_id)
    assert working_set.segments, "Working set should include analyzed segments"

    first_segment_id = working_set.segments[0].segment_id
    stash_result = app_state.context_manager.stash_segments([first_segment_id], project_id)
    assert first_segment_id in stash_result.stashed_segments
    assert stash_result.tokens_freed >= 0

    retrieved = app_state.context_manager.retrieve_stashed(
        query="Hello",
        filters={},
        project_id=project_id,
    )
    assert any(seg.segment_id == first_segment_id for seg in retrieved)


@pytest.mark.integration
def test_multi_project_isolation(app_state, sample_segments: list[ContextSegment]) -> None:
    """Verify working sets remain isolated across project boundaries."""
    other_project = "alt-project"
    now = datetime.now()

    # Seed primary project
    for segment in sample_segments:
        app_state.storage.store_segment(segment, segment.project_id)

    # Seed secondary project with distinct IDs
    secondary_segments = [
        ContextSegment(
            segment_id=f"secondary-{idx}",
            text=f"secondary text {idx}",
            type="note",
            project_id=other_project,
            task_id=None,
            created_at=now - timedelta(minutes=idx),
            last_touched_at=now - timedelta(minutes=idx),
            pinned=False,
            generation="young",
            gc_survival_count=0,
            refcount=0,
            file_path=None,
            line_range=None,
            tags=["secondary"],
            topic_id=None,
            tokens=3,
            tokens_computed_at=now - timedelta(minutes=idx),
            text_hash=None,
            tier="working",
        )
        for idx in range(3)
    ]

    for segment in secondary_segments:
        app_state.storage.store_segment(segment, segment.project_id)

    primary_working_set = app_state.context_manager.get_working_set("test-project")
    secondary_working_set = app_state.context_manager.get_working_set(other_project)

    assert {seg.segment_id for seg in primary_working_set.segments} == {
        "seg-message",
        "seg-log",
    }
    assert {seg.segment_id for seg in secondary_working_set.segments} == {
        "secondary-0",
        "secondary-1",
        "secondary-2",
    }

    # Stashing in one project must not affect the other
    app_state.context_manager.stash_segments(["secondary-0"], other_project)
    updated_primary = app_state.context_manager.get_working_set("test-project")
    assert {seg.segment_id for seg in updated_primary.segments} == {
        "seg-message",
        "seg-log",
    }
