# Demo Guide

This guide provides step-by-step demonstrations of the Out of Context MCP server capabilities.

---

## Demo Scenario 1: Long Debugging Session

This scenario demonstrates managing context during a long debugging session where context accumulates over time.

### Setup Instructions

1. **Start with a fresh project:**
   - Create a new project or use an existing one
   - Ensure the MCP server is running and connected

2. **Simulate a debugging session:**
   - Have the agent work on debugging a complex issue
   - Generate multiple messages, code snippets, and logs
   - Let context accumulate over 20-30 interactions

### Step-by-Step Demonstration

#### Step 1: Monitor Initial Context

**Action:** Call `context_analyze_usage`

```json
{
  "project_id": "debug-session"
}
```

**Expected Outcome:**
- Usage metrics showing current token count
- Health score indicating healthy state
- Low usage percentage (< 20%)

#### Step 2: Accumulate Context

**Action:** Continue debugging session, generating:
- Multiple code file reads
- Error logs and stack traces
- Debug messages
- Code changes and explanations

**Expected Outcome:**
- Context grows over time
- Multiple segments created
- Token count increases

#### Step 3: Monitor Growing Context

**Action:** Periodically call `context_analyze_usage` (every 10 interactions)

**Expected Outcome:**
- Usage percentage gradually increases
- Warnings appear when usage > 60%
- Recommendations suggest pruning when usage > 80%

#### Step 4: Analyze Pruning Candidates

**Action:** When usage > 80%, call `context_gc_analyze`

```json
{
  "project_id": "debug-session",
  "target_tokens": 50000
}
```

**Expected Outcome:**
- List of pruning candidates with scores
- Pruning plan showing segments to stash
- Estimated tokens that will be freed

#### Step 5: Review and Prune

**Action:** Review candidates, then call `context_gc_prune`

```json
{
  "project_id": "debug-session",
  "segment_ids": ["seg1", "seg2", "seg3"],
  "action": "stash"
}
```

**Expected Outcome:**
- Segments moved to stashed storage
- Tokens freed from working set
- Usage percentage decreases

#### Step 6: Verify Results

**Action:** Call `context_analyze_usage` again

**Expected Outcome:**
- Lower usage percentage
- Health score improved
- More remaining tokens available

### Success Criteria

- ✅ Context usage monitored throughout session
- ✅ Pruning candidates identified automatically
- ✅ Context pruned before hitting limits
- ✅ Important context preserved (pinned if needed)
- ✅ Session continues without interruption

---

## Demo Scenario 2: Multi-File Refactoring

This scenario demonstrates managing context when working across multiple files during a refactoring task.

### Setup Instructions

1. **Start with a project containing multiple files:**
   - Project with 5-10 source files
   - Files are related (e.g., same module or feature)

2. **Create a refactoring task:**
   - Use `context_set_current_task` to set task ID
   - Begin refactoring work across files

### Step-by-Step Demonstration

#### Step 1: Set Current Task

**Action:** Call `context_set_current_task`

```json
{
  "project_id": "refactoring-project",
  "task_id": "refactor-api-module"
}
```

**Expected Outcome:**
- Current task set to "refactor-api-module"
- Working set filtered to this task

#### Step 2: Work Across Multiple Files

**Action:** Have agent work on refactoring:
- Read multiple files
- Make changes across files
- Generate explanations and decisions

**Expected Outcome:**
- Segments created with `task_id: "refactor-api-module"`
- Context accumulates for this task
- Multiple file paths in segments

#### Step 3: Monitor Task Context

**Action:** Call `context_get_task_context`

```json
{
  "project_id": "refactoring-project",
  "task_id": "refactor-api-module"
}
```

**Expected Outcome:**
- All segments for this task listed
- Token count for task context
- Segments organized by file

#### Step 4: Stash Old Files

**Action:** When context grows, stash segments from completed files

```json
{
  "project_id": "refactoring-project",
  "filters": {
    "file_path": "src/old_module.py",
    "task_id": "refactor-api-module"
  }
}
```

**Expected Outcome:**
- Segments from old_module.py stashed
- Tokens freed from working set
- Context remains for active files

#### Step 5: Create Task Snapshot

**Action:** Before switching tasks, create snapshot

```json
{
  "project_id": "refactoring-project",
  "task_id": "refactor-api-module",
  "name": "before-switching-tasks"
}
```

**Expected Outcome:**
- Snapshot created with all task context
- Snapshot stored in stashed storage
- Can be retrieved later

#### Step 6: Switch Tasks

**Action:** Set new current task

```json
{
  "project_id": "refactoring-project",
  "task_id": "fix-bug-123"
}
```

**Expected Outcome:**
- Current task changed
- Working set updated for new task
- Previous task context preserved

#### Step 7: Retrieve Task Context

**Action:** Later, retrieve previous task context

```json
{
  "project_id": "refactoring-project",
  "query": "refactor-api-module",
  "move_to_active": true
}
```

**Expected Outcome:**
- Segments from previous task retrieved
- Segments moved back to active context
- Can continue work on previous task

### Success Criteria

- ✅ Task context organized and isolated
- ✅ Context switched between tasks smoothly
- ✅ Old task context preserved and retrievable
- ✅ Multi-file work managed efficiently
- ✅ No context loss when switching tasks

---

## Demo Scenario 3: Reproducing Context Overflow

This scenario demonstrates how to create an overflow situation and how the server helps resolve it.

### Setup Instructions

1. **Create a scenario with high context usage:**
   - Simulate a session with many interactions
   - Generate large amounts of context
   - Approach token limits intentionally

### Step-by-Step Demonstration

#### Step 1: Create High Context Usage

**Action:** Generate context until usage > 90%

**Methods:**
- Read many large files
- Generate verbose logs
- Create many segments
- Accumulate context over time

**Expected Outcome:**
- Context usage approaches limits
- Many segments in working set
- High token count

#### Step 2: Observe Overflow Symptoms

**Action:** Call `context_analyze_usage`

**Expected Outcome:**
- Usage percentage > 90%
- **URGENT** warning displayed
- Health score low
- Urgent recommendations

#### Step 3: Analyze Pruning Candidates

**Action:** Call `context_gc_analyze` with target tokens

```json
{
  "project_id": "overflow-demo",
  "target_tokens": 100000
}
```

**Expected Outcome:**
- Many pruning candidates identified
- Pruning plan generated
- Clear path to free space

#### Step 4: Pin Important Segments

**Action:** Before pruning, pin critical segments

```json
{
  "project_id": "overflow-demo",
  "segment_ids": ["important-seg1", "important-seg2"]
}
```

**Expected Outcome:**
- Important segments pinned
- Protected from pruning
- Will not be included in pruning plan

#### Step 5: Execute Pruning Plan

**Action:** Call `context_gc_prune` with plan segments

```json
{
  "project_id": "overflow-demo",
  "segment_ids": ["old-seg1", "old-seg2", "log-seg1"],
  "action": "stash"
}
```

**Expected Outcome:**
- Segments stashed
- Tokens freed
- Usage percentage decreases
- Overflow resolved

#### Step 6: Verify Resolution

**Action:** Call `context_analyze_usage` again

**Expected Outcome:**
- Usage percentage < 80%
- Health score improved
- Warnings cleared
- System healthy again

### How Server Solves Overflow

1. **Proactive Monitoring:** Warnings at 60%, 80%, 90% thresholds
2. **Automatic Candidate Identification:** GC heuristics find candidates
3. **Pruning Plans:** Generate plans to free specific token amounts
4. **Safe Pruning:** Pin protection prevents losing important context
5. **Stashing:** Archive instead of delete for later retrieval

### Success Criteria

- ✅ Overflow situation created and detected
- ✅ Pruning candidates identified automatically
- ✅ Important context protected (pinned)
- ✅ Overflow resolved without data loss
- ✅ System returns to healthy state

---

## Demo Scripts

### Manual Demo Checklist

Use this checklist for manual demonstrations:

**Setup:**
- [ ] MCP server installed and running
- [ ] Project directory accessible
- [ ] Storage directory writable
- [ ] Test project created

**Monitoring:**
- [ ] `context_analyze_usage` works
- [ ] Usage metrics displayed correctly
- [ ] Health score calculated
- [ ] Warnings appear at thresholds

**Pruning:**
- [ ] `context_gc_analyze` identifies candidates
- [ ] Pruning plan generated with target_tokens
- [ ] `context_gc_pin` protects segments
- [ ] `context_gc_prune` executes successfully

**Stashing:**
- [ ] `context_stash` moves segments
- [ ] `context_search_stashed` finds segments
- [ ] `context_retrieve_stashed` retrieves segments
- [ ] `move_to_active` restores to working set

**Task Management:**
- [ ] `context_set_current_task` switches tasks
- [ ] `context_get_task_context` shows task segments
- [ ] `context_create_task_snapshot` creates snapshots
- [ ] Task context isolated correctly

**Verification:**
- [ ] All tools return expected results
- [ ] Error handling works correctly
- [ ] Storage persists across sessions
- [ ] Performance acceptable

---

## Tips for Successful Demos

### Preparation

1. **Test environment:** Ensure server is working before demo
2. **Sample data:** Prepare sample projects with realistic context
3. **Script:** Have a script or outline ready
4. **Backup:** Backup storage directory before demo

### During Demo

1. **Explain context:** Explain what each tool does before calling
2. **Show results:** Display tool results clearly
3. **Handle errors:** If errors occur, explain and recover
4. **Pace:** Don't rush - let audience see each step

### Common Issues

**Server not responding:**
- Check server logs
- Verify MCP connection
- Restart server if needed

**Unexpected results:**
- Check project_id matches
- Verify segments exist
- Review error messages

**Performance issues:**
- Use smaller datasets for demo
- Explain scalability features
- Show that indexing helps

---

## Next Steps

After completing demos:

1. **Review results:** Analyze what worked and what didn't
2. **Collect feedback:** Get feedback from audience
3. **Update documentation:** Improve docs based on demo experience
4. **Refine scenarios:** Adjust scenarios for better demonstrations

See [Usage Guide](usage.md) for detailed usage instructions and [API Documentation](api/tools.md) for tool reference.

