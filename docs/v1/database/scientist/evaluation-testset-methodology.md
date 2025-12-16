# Evaluation Test Set Methodology

**Version:** 1.0.0  
**Date:** 2024-12-16  
**Author:** ML Scientist  
**Test Set:** evaluation-testset.json (55 queries)

---

## Overview

This document describes the methodology used to create the evaluation test set for validating semantic search quality improvements over the baseline substring search.

---

## Objectives

1. **Measure baseline performance** - Establish current substring search capabilities
2. **Validate semantic search improvement** - Quantify quality gains from embeddings
3. **Ensure representative coverage** - Include realistic usage patterns
4. **Enable reproducible evaluation** - Standardized test set for consistent measurement

---

## Query Collection Process

### Step 1: Source Analysis (30 minutes)

**Available Contexts:**
- project-overview.mdc
- persona-definitions.mdc
- decision-log.mdc
- current-status.mdc
- key-documents-index.mdc

**Total Content:** ~5 contexts with comprehensive project documentation

**Use Case Analysis:**
- **Primary users:** AI agents working across multiple sessions
- **Common tasks:** Understanding project status, retrieving requirements, following workflows
- **Typical queries:** How-to questions, status checks, requirement lookups, decision history

### Step 2: Query Generation Strategy (2-3 hours)

**Four Query Categories:**

1. **How-To Queries (40% - 22 queries)**
   - Procedural questions about workflows
   - Action-oriented tasks
   - Examples: "How do I create a context?", "How do I handle stale contexts?"
   
2. **Factual/Definition Queries (30% - 17 queries)**
   - Information retrieval
   - Concept definitions
   - Status checks
   - Examples: "What is the MVP scope?", "What embedding model are we using?"

3. **Troubleshooting Queries (20% - 11 queries)**
   - Problem scenarios
   - Error handling
   - Edge cases
   - Examples: "Context conflicts with git", "Contexts severely outdated"

4. **Comparison Queries (10% - 5 queries)**
   - Comparative analysis
   - Decision tradeoffs
   - Role distinctions
   - Examples: "Storage vs retrieval limits", "Scientist vs developer responsibilities"

**Query Creation Principles:**
- ✅ Natural language (as users would actually ask)
- ✅ Varied specificity (broad + narrow queries)
- ✅ Different difficulty levels
- ✅ Include queries baseline handles well (detect regressions)
- ✅ Include queries requiring semantic understanding (synonyms, paraphrases)
- ❌ No artificial bias toward semantic search
- ❌ No overly technical jargon unless realistic

### Step 3: Relevance Judgment Process (2 hours)

**Judgment Criteria:**

**Relevant (included in relevant_contexts):**
- Context directly answers the query
- Context provides necessary background information
- Context includes the answer as part of a larger discussion
- Context would help user accomplish the task in the query

**Not Relevant (excluded):**
- Context only tangentially related
- Context mentions query terms but doesn't help answer
- Context is about different topic despite keyword overlap
- Context would not help user accomplish the task

**Process:**
1. Read each query carefully
2. Review all 5 available contexts
3. Identify which contexts contain relevant information
4. Record context names in relevant_contexts array
5. Add notes explaining query intent or edge cases

**Judgment Consistency:**
- Applied same criteria across all queries
- When uncertain, erred toward inclusion (if somewhat relevant, include it)
- Most queries have 1-2 relevant contexts (aligned with available content)
- Some queries (e.g., onboarding) have 2-3 relevant contexts (multiple docs helpful)

---

## Query Type Distribution

### Actual Distribution

| Category | Target | Actual | Percentage |
|----------|--------|--------|------------|
| How-To | 40% | 22 | 40.0% |
| Factual | 30% | 17 | 30.9% |
| Troubleshooting | 20% | 11 | 20.0% |
| Comparison | 10% | 5 | 9.1% |
| **Total** | **100%** | **55** | **100%** |

✅ Distribution closely matches target specifications

### Query Complexity Levels

**Easy (15 queries):** Single-context answers, explicit keyword matches
- Examples: "What file format are contexts stored in?", "What is the next action?"

**Medium (30 queries):** Multi-context answers, some inference required
- Examples: "How do I set up context management?", "What are acceptance criteria?"

**Hard (10 queries):** Semantic understanding required, paraphrase/synonym-based
- Examples: "Context says Week 1 but we're in Week 3", "Should I fetch all 100 contexts?"

---

## Coverage Analysis

### Topic Coverage

**Project Structure & Overview:**
- ✅ 8 queries covering project understanding, architecture, technical details

**Context Management Workflows:**
- ✅ 15 queries covering CRUD operations, lifecycle, staleness handling

**Personas & Roles:**
- ✅ 7 queries covering scientist/developer distinctions, responsibilities

**Requirements & Decisions:**
- ✅ 12 queries covering MVP scope, constraints, decision rationale

**Status & Planning:**
- ✅ 8 queries covering current status, next actions, timeline

**Documentation & Navigation:**
- ✅ 5 queries covering document discovery, onboarding

**Total:** 55 queries providing comprehensive coverage

### Edge Cases Included

1. **Staleness scenarios:** Queries about detecting and recovering from stale contexts
2. **Scale scenarios:** "I have 100 contexts - should I fetch them all?"
3. **Conflict resolution:** "Context conflicts with git history"
4. **Maintenance:** Context cleanup, deletion lifecycle
5. **Onboarding:** New user workflows, getting started queries

---

## Quality Validation

### Self-Review Checklist

- ✅ Test set has 55 queries (exceeds 50 minimum)
- ✅ All queries have relevance judgments
- ✅ Query type distribution matches specifications (40/30/20/10)
- ✅ Queries use natural language
- ✅ Coverage includes all major topics
- ✅ Edge cases included
- ✅ No obvious bias toward semantic search
- ✅ Includes queries baseline should handle well
- ✅ Metadata complete (IDs, types, notes)

### Statistical Properties

**Query Characteristics:**
- Average relevant contexts per query: 1.5
- Queries with 1 relevant context: 32 (58%)
- Queries with 2 relevant contexts: 18 (33%)
- Queries with 3 relevant contexts: 5 (9%)
- Queries with 0 relevant contexts: 0 (0%)

**Rationale for distribution:**
- Most queries have 1-2 relevant contexts (realistic for focused questions)
- Some queries span multiple contexts (onboarding, comprehensive topics)
- No queries with 0 relevant contexts (all queries answerable from available content)

---

## Expected Baseline Performance

### Predictions

**Expected High Performance (substring matching sufficient):**
- Queries with exact keyword matches: "What is semantic search?", "What embedding model?"
- Simple factual queries: "What is the next action?", "What file format?"

**Expected Low Performance (semantic understanding required):**
- Paraphrase queries: "Context says Week 1 but we're in Week 3" (staleness)
- Synonym queries: "How to set up" vs "How to initialize/configure"
- Conceptual queries: "Two-persona approach" vs "scientist and developer roles"
- Problem scenarios: "Contexts severely outdated" vs "staleness"

**Baseline Strengths:**
- Exact term matching
- Simple keyword overlap
- Short queries with specific terms

**Baseline Weaknesses:**
- Paraphrases and synonyms
- Conceptual similarity without keyword overlap
- Troubleshooting scenarios (symptom vs solution vocabulary mismatch)
- Comparison queries (require understanding relationships, not just keywords)

---

## Limitations and Biases

### Known Limitations

1. **Limited context diversity:**
   - Only 5 contexts available
   - All contexts related to single project (database enhancement)
   - May not reflect full production usage diversity

2. **Query creation bias:**
   - Queries created by single author
   - Based on anticipated usage, not actual usage logs
   - May not capture all real-world query patterns

3. **Relevance judgment subjectivity:**
   - Binary relevance (relevant/not relevant) is simplified
   - Some contexts borderline relevant but included
   - Real users may have different relevance expectations

4. **Test set size:**
   - 55 queries is modest (industrial benchmarks often 100-500+)
   - Sufficient for MVP validation but may have statistical noise
   - Results should be interpreted with confidence intervals

### Mitigation Strategies

1. **Diverse query types:** Included 4 categories, 3 difficulty levels
2. **Comprehensive coverage:** All major topics covered
3. **Edge cases:** Included troubleshooting and scale scenarios
4. **Documentation:** Clearly documented methodology and judgment criteria
5. **Peer review option:** Test set can be reviewed by developer for alignment

### Future Improvements

**For Phase 2 (if needed):**
- Expand to 100+ queries with actual usage logs
- Add graded relevance (highly relevant, relevant, marginally relevant)
- Include query variations (same intent, different phrasing)
- Add adversarial queries (designed to stress-test semantic search)
- Multi-annotator agreement for reliability

---

## Expected Results

### Baseline (Substring Search)

**Predicted Performance:**
- Precision@5: 0.40 - 0.60 (moderate)
- Recall@5: 0.30 - 0.50 (limited by keyword matching)
- MRR: 0.50 - 0.70 (good for exact matches)

**Rationale:**
- Many queries have explicit keywords (will match)
- Some queries require semantic understanding (will fail)
- Small context corpus (limits noise, helps precision)

### Semantic Search Target

**Target Performance (30% improvement):**
- Precision@5: 0.52 - 0.78 (30% relative improvement)
- Recall@5: 0.39 - 0.65 (30% relative improvement)
- MRR: 0.65 - 0.91 (30% relative improvement)

**Expected Improvements:**
- Paraphrase queries: Large gains
- Synonym queries: Large gains
- Conceptual queries: Moderate gains
- Exact match queries: Minimal change (already good)

**Validation:**
- Paired t-test for statistical significance (p < 0.05)
- Per-category analysis (ensure no regressions)
- Qualitative review of failure modes

---

## Usage Instructions

### For Baseline Evaluation (Action Item 02)

1. Load test set: `evaluation-testset.json`
2. For each query:
   - Query current MCP server (substring search)
   - Retrieve top 5 results
   - Calculate precision based on relevant_contexts
3. Aggregate metrics: P@5, R@5, MRR, NDCG@10
4. Document results: `baseline-results.json`

### For Semantic Search Evaluation (Action Item 03)

1. Load same test set: `evaluation-testset.json`
2. For each query:
   - Query semantic search API
   - Retrieve top 5 results
   - Calculate precision based on relevant_contexts
3. Aggregate metrics: P@5, R@5, MRR, NDCG@10
4. Document results: `semantic-results.json`
5. Compare to baseline with statistical significance test

---

## Reproducibility

### Version Control

- Test set: `evaluation-testset.json` (tracked in git)
- Methodology: This document (tracked in git)
- Evaluation scripts: `evaluate.py` (to be created in Action Item 02)

### Reproducibility Checklist

- ✅ Test set version controlled
- ✅ Methodology documented
- ✅ Relevance judgments explicit
- ✅ Query IDs for traceability
- ✅ Metadata includes creation date, author, version

**Anyone can reproduce evaluation by:**
1. Checking out git repository
2. Loading `evaluation-testset.json`
3. Running `evaluate.py` with same MCP server state
4. Comparing results to documented baseline/semantic benchmarks

---

## Validation Against Requirements

### RT-10 Compliance

From requirements.md Section 7.2 (RT-10):

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Minimum 50 queries | ✅ | 55 queries created |
| Representative of LLM usage | ✅ | Based on MCP context management workflows |
| Binary relevance judgments | ✅ | Each query has relevant_contexts array |
| Diverse query types | ✅ | 4 categories (how-to, factual, troubleshooting, comparison) |
| Documented methodology | ✅ | This document |

**Conclusion:** Test set fully complies with RT-10 specifications.

---

## Sign-Off

**Status:** ✅ Complete  
**Date:** 2024-12-16  
**Scientist:** ML Scientist Persona  

**Next Actions:**
1. Proceed to Action Item 02 (Baseline Evaluation)
2. Share test set with developer for alignment review (optional)
3. Begin implementing evaluation script (`evaluate.py`)

**Files Delivered:**
- `evaluation-testset.json` (55 queries with relevance judgments)
- `evaluation-testset-methodology.md` (this document)

---

**Last Updated:** 2024-12-16

