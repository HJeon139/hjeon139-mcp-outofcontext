# Context Management Setup Complete

**Date:** 2024-12-16  
**Status:** ✅ Production Ready

---

## What Was Set Up

### 1. MCP Context Documents (5 total)

Stored in `.out_of_context/contexts/` and tracked in git:

| Context | Purpose | Size | Update Frequency |
|---------|---------|------|------------------|
| `project-overview` | Project summary, constraints, stack | ~300 lines | Rare (scope change) |
| `persona-definitions` | Scientist vs Developer roles | ~150 lines | Rare (role change) |
| `decision-log` | Key decisions with rationale | ~250 lines | After decisions |
| `current-status` | Progress, next actions, blockers | ~200 lines | After each session |
| `key-documents-index` | Navigation to all docs | ~150 lines | When docs added |

**Total Storage:** ~1,050 lines ≈ **3-4k tokens**

### 2. Cursor Rules

**File:** `.cursor/rules/context-management.mdc`

**Key Features:**
- ✅ Always applies (priority: high, applies: always)
- ✅ Session start/end checklist
- ✅ Fetching guidelines (selective, < 10 contexts)
- ✅ Staleness detection and handling
- ✅ Storage vs retrieval distinction clarified
- ✅ Recovery procedures for inconsistent contexts

### 3. Git Integration

**Modified:** `.gitignore`

**Changes:**
```gitignore
# Storage and runtime data
.out_of_context/
# But include context documents for cross-session continuity
!.out_of_context/contexts/
!.out_of_context/contexts/*.mdc
```

**Result:** Context documents now tracked in git, preserved across clones

### 4. Cleanup

**Deleted obsolete test contexts:**
- `test-single-pydantic` ❌
- `batch-test-3` ❌

**Remaining contexts:** 5 production contexts only

---

## Key Improvements from Feedback

### 1. ✅ Cleanup Complete
- Deleted test contexts
- Only production contexts remain

### 2. ✅ Git Integration
- Contexts now tracked in version control
- Team can share contexts across machines
- Context history preserved

### 3. ✅ Rule Always Applies
- Added `applies: always` to frontmatter
- Added prominent checklist at top
- Clear "ALWAYS APPLY" notice

### 4. ✅ Storage vs Retrieval Clarified

**Old Understanding (Incorrect):**
- < 10 contexts total (limiting storage)

**New Understanding (Correct):**
- **Storage:** Unlimited (store as needed)
- **Retrieval:** < 10 contexts per session (< 20k tokens into context window)
- **Strategy:** Store liberally, fetch conservatively

**Practical Example:**
```
Stored: 50 contexts (covering all project phases)
Fetched: 3-5 contexts (only relevant to current task)
Result: Full project history available, but context window not flooded
```

### 5. ✅ Staleness Handling

**New Section Added:** "Handling Stale or Inconsistent Context"

**Covers:**
- How to detect staleness (check `last-updated`, cross-reference with git)
- How to handle inconsistencies (verify ground truth, update or flag)
- Common scenarios (completed action items not updated, conflicting contexts)
- Recovery procedures (rebuild from git history if severely outdated)
- Prevention best practices (update at session end, date stamp decisions)

**Key Principle:** **Git is ground truth** - if context conflicts with git, trust git and update context

---

## Usage Guide

### Starting a New Session

```bash
# AI agent automatically fetches
get_context names=["project-overview", "current-status"]

# Summarizes project state
# Asks: "Are you scientist or developer?"

# Fetches role-specific contexts
get_context names=["persona-definitions", "key-documents-index"]
```

**Total tokens fetched:** ~5k (well under limit)

### During Work

```bash
# Make a decision → update decision-log
put_context(name="decision-log", text="[append decision with date]")

# Complete action item → update current-status
put_context(name="current-status", text="[mark item complete]")
```

### Ending Session

```bash
# Verify contexts updated
get_context names=["current-status"]

# Check against reality
ls docs/v1/database/scientist/  # Files match what context says?

# If inconsistent, update before ending
put_context(name="current-status", text="[correct info]")
```

---

## Fetching Best Practices

### ✅ Good Fetching Patterns

```bash
# Specific names (recommended)
get_context names=["project-overview", "current-status"]

# Limited list (if needed)
list_context limit=10

# Targeted search
search_context query="database decision" limit=5
```

### ❌ Bad Fetching Patterns

```bash
# Fetching everything (floods context window)
list_context  # May return 50+ contexts

# Broad search (returns too many)
search_context query="project"  # Too generic

# Getting all contexts
get_context names=[...50 contexts...]  # 100k tokens!
```

---

## Staleness Detection Examples

### Example 1: Outdated Status

**Symptom:** Context says "Week 1" but git shows 3 weeks of commits

**Detection:**
```bash
git log --oneline --since="3 weeks ago" | wc -l
# Returns: 45 commits

get_context names=["current-status"]
# Shows: "Week 1, Developer Action Item 01"
```

**Resolution:**
```bash
# Rebuild current-status from git history
put_context(
  name="current-status",
  text="Week 3. Completed: DB choice, MVP implementation. Current: Performance validation.",
  metadata={"last-updated": "2024-12-16", "phase": "validation"}
)
```

### Example 2: Missing Decision

**Symptom:** Git shows ChromaDB implementation but decision-log says "pending"

**Detection:**
```bash
grep -r "chromadb" src/
# Returns: Multiple files using ChromaDB

get_context names=["decision-log"]
# Shows: "Vector database: TBD (RT-3 pending)"
```

**Resolution:**
```bash
# Backfill decision-log
put_context(
  name="decision-log",
  text="[existing log]\n\n## 2024-12-10: Vector Database Choice\n- Chose: ChromaDB\n- Rationale: [infer from code/docs]\n- Status: Implemented"
)
```

---

## Context Lifecycle

### Phase 1: Requirements (Complete)
```
Active: 5 core contexts
Fetch at start: 2-3 contexts
Total tokens: < 5k
```

### Phase 2: Implementation (Current)
```
Active: 5 core + 3 phase contexts = 8 total
Fetch at start: 2-3 contexts (core)
Fetch when needed: 1-2 phase contexts
Total tokens: < 10k typically
```

### Phase 3: Phase 2 Planning (Future)
```
Active: 5 core + 5 phase2 contexts = 10 total
Archive: Phase 1 detailed contexts (keep in git, remove from MCP)
Fetch at start: 2-3 contexts
Total tokens: < 10k
```

### Long-Term (Multiple Phases)
```
Stored: 20-50 contexts (all phases documented)
Active (fetched): 3-5 contexts per session
Archive old phases: Delete from MCP after documenting in git
Strategy: Store full history, fetch only relevant
```

---

## Verification Checklist

- [x] 5 production contexts created and stored
- [x] Test contexts deleted
- [x] Contexts tracked in git (`.gitignore` updated)
- [x] Cursor rule created (`.cursor/rules/context-management.mdc`)
- [x] Rule marked as "always applies"
- [x] Storage vs retrieval distinction clarified
- [x] Staleness handling documented
- [x] Session start/end checklists added
- [x] Fetching best practices documented
- [x] Recovery procedures defined

---

## Next Steps

### For Next Session

1. **Test context fetching:**
   ```bash
   get_context names=["project-overview", "current-status"]
   ```

2. **Verify no flooding:**
   - Should get ~5k tokens total
   - Should NOT flood context window

3. **Update after work:**
   ```bash
   put_context(name="current-status", text="[progress update]")
   ```

### For Team Onboarding

1. Clone repo → contexts come with it (tracked in git)
2. Read `.cursor/rules/context-management.mdc`
3. Fetch `project-overview` + `current-status` to understand project
4. Start working based on `current-status` next actions

### For Long-Term Maintenance

- **Weekly:** Review context staleness during active development
- **Monthly:** Archive completed phase contexts
- **After milestones:** Create retrospective context, archive phase details

---

## Success Metrics

**Before Context Management:**
- ❌ Start each session from scratch
- ❌ Re-read 100+ pages of docs
- ❌ Lose decisions across sessions
- ❌ No team context sharing

**After Context Management:**
- ✅ Fetch 2 contexts → understand in 30 seconds
- ✅ Decisions preserved across sessions
- ✅ Clear role boundaries (scientist/developer)
- ✅ Team shares contexts via git
- ✅ Multi-week continuity maintained

---

## Files Created/Modified

### Created
1. `.out_of_context/contexts/project-overview.mdc`
2. `.out_of_context/contexts/persona-definitions.mdc`
3. `.out_of_context/contexts/decision-log.mdc`
4. `.out_of_context/contexts/current-status.mdc`
5. `.out_of_context/contexts/key-documents-index.mdc`
6. `.cursor/rules/context-management.mdc`
7. `docs/v1/database/CONTEXT-MANAGEMENT-SETUP.md` (this file)

### Modified
1. `.gitignore` - Added exception for `.out_of_context/contexts/`

### Deleted
1. `.out_of_context/contexts/test-single-pydantic.mdc`
2. `.out_of_context/contexts/batch-test-3.mdc`

---

**Status:** ✅ Ready for Production Use

Test it now:
```bash
get_context names=["project-overview", "current-status"]
```

