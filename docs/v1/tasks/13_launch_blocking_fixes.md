# Task 13: Launch Blocking Fixes

## Dependencies

- Task 10: MCP Server Integration
- Task 06: Monitoring Tools
- Task 07: Pruning Tools

## Scope

Fix the launch-blocking bugs identified in pre-launch review:
1. **Proactive limit warnings** (requirement #5): Ensure the MCP server provides proactive suggestions/notifications when context approaches limits
2. **Cross-session stash retrieval**: Enable retrieval of stashed context across different chat windows/sessions by adding project discovery functionality
3. **Token limit defaults**: Fix system to use 1 million token limit from config instead of hardcoded 32k defaults throughout codebase

## Acceptance Criteria

- `context_analyze_usage` includes warnings when usage crosses configurable thresholds (60%, 80%, 90%)
- Warnings include recommended follow-up tool calls (e.g., `context_stash` with candidate IDs)
- Tool descriptions include threshold guidance and reminders to check usage periodically
- Response format includes clear impact summaries and next-step guidance
- No new dependencies added (prompt engineering and response formatting only)

## Implementation Details

### 1. Add Threshold Configuration

**Location**: `src/hjeon139_mcp_outofcontext/config.py` or `analysis_engine.py`

Add configurable thresholds:
- Warning threshold: 60% (early warning)
- High threshold: 80% (action recommended)
- Urgent threshold: 90% (immediate action required)

These can be:
- Environment variables (e.g., `CONTEXT_WARNING_THRESHOLD=60`)
- Configuration file settings
- Default values if not configured

### 2. Enhance `context_analyze_usage` Response

**Location**: `src/hjeon139_mcp_outofcontext/tools/monitoring.py`

Modify `handle_analyze_usage` to:

1. **Check thresholds** and add warnings:
   ```python
   if metrics.usage_percent >= 90.0:
       warnings.append("URGENT: Context usage at 90%+ - prune immediately")
   elif metrics.usage_percent >= 80.0:
       warnings.append("HIGH: Context usage at 80%+ - consider pruning")
   elif metrics.usage_percent >= 60.0:
       warnings.append("WARNING: Context usage at 60%+ - monitor closely")
   ```

2. **Include recommended actions** in response:
   - When usage is high, suggest specific tool calls
   - Include segment IDs for pruning/stashing candidates
   - Provide estimated token savings

3. **Add impact summary**:
   - "After stashing X segments, usage will drop to Y%"
   - "Pruning candidates: N segments, M tokens"

### 3. Update Tool Descriptions

**Location**: `src/hjeon139_mcp_outofcontext/tools/monitoring.py`

Update `context_analyze_usage` tool description to include:
- Threshold guidance (check at 60%, 80%, 90%)
- Reminder to run periodically
- Quick-start example: "Call with project_id='my-project' to check usage. If usage > 60%, consider stashing/pruning."

### 4. Enhance Recommendation Generation

**Location**: `src/hjeon139_mcp_outofcontext/analysis_engine.py`

Modify `generate_recommendations` to:
- Add 60% threshold warning (currently only 80% and 90%)
- Include more actionable guidance
- Provide estimated impact (tokens freed, usage reduction)

### 5. Response Format Enhancement

**Location**: `src/hjeon139_mcp_outofcontext/tools/monitoring.py`

Enhance response dictionary to include:
```python
{
    "usage_metrics": {...},
    "health_score": {...},
    "recommendations": [...],
    "warnings": [...],  # NEW: Threshold-based warnings
    "suggested_actions": [...],  # NEW: Specific tool calls with parameters
    "impact_summary": {...},  # NEW: Estimated impact of actions
    "pruning_candidates_count": ...
}
```

## Testing

- Test with usage at various thresholds (50%, 60%, 80%, 90%)
- Verify warnings appear at correct thresholds
- Verify suggested actions include valid segment IDs
- Verify impact summaries are accurate
- Test with empty working set (no false warnings)

## Related Bugs

- `docs/v1/bugs/2025-12-08-missing-proactive-limit-warnings.md` - This task addresses this bug
- `docs/v1/bugs/2025-12-08-tool-feedback-lacks-impact.md` - Partially addressed (impact summaries)
- `docs/v1/bugs/2025-12-08-no-cross-session-stash-retrieval.md` - **LAUNCH BLOCKER**: Cannot retrieve stashed context across sessions
- `docs/v1/bugs/2025-12-08-token-limit-defaults-to-32k-instead-of-1m.md` - **LAUNCH BLOCKER**: System defaults to 32k tokens instead of 1 million

## References

- [Requirements](../../v0/requirements.md) - Requirement #5: Proactive suggestions/notifications
- [Launch Blocking Analysis](../bugs/LAUNCH_BLOCKING_ANALYSIS.md) - Original analysis
- [Bug Report](../bugs/2025-12-08-missing-proactive-limit-warnings.md) - Detailed bug description

