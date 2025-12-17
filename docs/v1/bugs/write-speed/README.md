# Bug Investigation: Slow Write Performance

**Issue:** `put_context` MCP tool is 20-60x slower than direct file operations  
**Date Reported:** 2024-12-16  
**Status:** Investigation complete, recommendation pending approval  
**Severity:** Medium (impacts UX but not blocking)

---

## Quick Summary

**Problem:** Writing contexts via `put_context` takes 1-3 seconds per call (vs 20-50ms for direct file writes)

**Root Cause:** MCP protocol overhead (70-150ms baseline, 1-3s under system load)

**Recommendation:** Remove MCP CRUD tools, use direct file operations (20-60x faster + simpler architecture)

---

## Documents in This Investigation

### 1. [bug-report.md](bug-report.md)
**From:** Customer perspective  
**Content:**
- User experience impact
- Performance observations
- Comparison with direct file operations
- Questions about need for MCP abstraction

**Key Finding:** Direct file ops feel instant, MCP tools feel sluggish

---

### 2. [root-cause.md](root-cause.md)
**From:** Engineering analysis  
**Content:**
- Code review of storage layer
- Performance profiling
- Bottleneck identification (MCP protocol, not storage)
- Impact on database integration

**Key Finding:** Storage layer is fast (~10-20ms), MCP overhead is the bottleneck (~70-150ms base, 1-3s under load)

---

### 3. [recommendations.md](recommendations.md)
**From:** Architecture proposal  
**Content:**
- Three options evaluated (Direct file ops, Optimize MCP, Hybrid)
- Recommendation: Remove MCP CRUD tools
- Implementation plan
- Impact on database integration design
- Risk assessment

**Key Recommendation:** Adopt Option A (direct file operations) - 20-60x faster, simpler architecture

---

## Key Insights

### 1. LLM Capability Evolution (2024)
Modern LLMs (GPT-4, Claude 3.5+) excel at:
- ✅ Understanding YAML frontmatter
- ✅ Creating/editing markdown files
- ✅ Direct file system operations
- ✅ Handling structured formats without abstraction

**Implication:** We don't need MCP tool abstractions anymore for simple file operations.

---

### 2. Database Integration Synergy
If we're building a file watcher for vector DB integration:

**Current (redundant):**
```
MCP tools → .mdc files → File watcher → Vector DB
```

**Proposed (unified):**
```
Direct file ops → .mdc files → File watcher → Vector DB
```

**Benefit:** File watcher becomes single source of truth (no redundancy)

---

### 3. Performance Impact
| Operation | MCP Tools | Direct File Ops | Improvement |
|-----------|-----------|----------------|-------------|
| Write context | 1-3s | 20-50ms | **20-60x** |
| Read context | 500ms-1s | 10-20ms | **25-100x** |
| Search (future) | N/A | 10-50ms (vector DB) | Much faster |

**User Experience:** Operations feel instant vs sluggish

---

## Recommendation Summary

### 🎯 Proposed Architecture Change

**Remove:**
- ❌ `put_context` MCP tool
- ❌ `get_context` MCP tool
- ❌ `list_context` MCP tool
- ❌ `delete_context` MCP tool
- ❌ `MDCStorage` abstraction layer

**Keep/Add:**
- ✅ Direct file operations (write, search_replace, read_file, delete_file)
- ✅ File watcher (with validation)
- ✅ `semantic_search` MCP tool (queries vector DB)
- ✅ Vector DB layer

**New Workflow:**
```python
# Instead of:
put_context("my-context", text="...", metadata={"type": "info"})

# LLM does:
write(".out_of_context/contexts/my-context.mdc", """---
name: my-context
type: info
created_at: 2024-12-16T10:00:00
---

Content here...
""")
```

---

## Impact on Database Integration (Dev 01)

### Design Document Updates Needed

1. **Remove Component:** CRUD MCP tools
2. **Enhance Component:** File watcher (add validation)
3. **Update Component:** Semantic search tool (queries vector DB)
4. **New Section:** `.mdc` format specification for LLMs

### Simplified Architecture

**Before:**
```
4 CRUD tools + Storage layer + File watcher + Vector DB = Complex
```

**After:**
```
File watcher + Vector DB + 1 search tool = Simple
```

**Benefit:** Fewer components, cleaner design, faster performance

---

## Implementation Plan

### Phase 1: Database Integration (Current - Dev 03-09)
Build file watcher + vector DB as planned (with enhanced validation)

### Phase 2: Migration (After MVP)
- Document `.mdc` format for LLMs
- Deprecate CRUD tools (keep for 1 release)
- Update examples and documentation

### Phase 3: Removal (Version 2.0)
- Remove CRUD MCP tools
- Simplify codebase
- Full cutover to direct file operations

---

## Decision Required

**Question:** Should we adopt this architecture change?

**Options:**
- ✅ **Option A:** Yes, remove CRUD tools (recommended)
  - Faster (20-60x)
  - Simpler
  - Better DB integration fit
  
- ❌ **Option B:** No, optimize MCP protocol
  - Still slower (2-3x improvement at best)
  - More complexity
  - High effort, low benefit

**Recommendation:** Adopt Option A

---

## Next Steps (If Approved)

1. **Update Dev 01:** Revise design document to reflect new architecture
2. **Simplify Dev 03-09:** Remove CRUD tool implementation, enhance file watcher
3. **Document Format:** Create `.mdc` format spec for LLMs
4. **Continue MVP:** Build file watcher + vector DB as planned

---

## Files in This Directory

- `README.md` - This file (summary and navigation)
- `bug-report.md` - Customer perspective, UX impact
- `root-cause.md` - Engineering analysis, profiling
- `recommendations.md` - Architecture proposal, implementation plan

---

## References

- Original context: `current-status` MCP context
- Database design: `docs/v1/database/developer/` (to be updated)
- Requirements: `docs/v1/database/requirements.md`

---

**Status:** ✅ Investigation complete, awaiting architectural decision  
**Recommendation:** Adopt Option A (remove CRUD tools, use direct file operations)  
**Impact:** Update Developer Action Item 01 (Design Document) before proceeding with implementation

