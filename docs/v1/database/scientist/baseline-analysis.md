# Baseline Performance Analysis

**Evaluation Date:** 2024-12-16  
**Search Method:** Word-based substring search  
**Test Set:** evaluation-testset.json v1.0.0 (55 queries)  
**Contexts:** 6 contexts (5 original + 1 added context-management)

---

## Executive Summary

The baseline word-based substring search achieves **moderate performance** with significant room for improvement:

- ✅ **High Recall (94.5%)** - Finds most relevant documents
- ❌ **Low Precision (25.5%)** - Returns many irrelevant documents
- ⚠️ **Moderate Ranking (MRR 65.2%)** - Relevant results appear mid-list
- ⚠️ **Good NDCG (74.2%)** - Decent but improvable ranking quality

**Key Insight:** The baseline has a "shotgun" approach - it finds relevant documents but buries them among irrelevant results. **Semantic search should significantly improve precision** by better understanding query intent.

---

## Overall Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Precision@5** | 0.255 | Of top 5 results, only 1.3 are relevant on average |
| **Recall@5** | 0.945 | Finds 94.5% of all relevant documents |
| **MRR** | 0.652 | First relevant result appears around position 2-3 |
| **NDCG@10** | 0.742 | Ranking quality is good but not optimal |

### What These Numbers Mean

**Precision@5 = 0.255 (LOW)**
- User gets ~1 relevant doc for every 4 results shown
- High noise-to-signal ratio
- Users must sift through irrelevant results

**Recall@5 = 0.945 (HIGH)**
- System doesn't miss many relevant documents
- Good coverage of the corpus
- Problem is not missing docs, but including too many

**MRR = 0.652 (MODERATE)**
- Relevant results appear around positions 2-3
- Not terrible, but users still need to scroll
- Better than random but not optimal

**NDCG@10 = 0.742 (GOOD)**
- Ranking is better than random
- Relevant docs tend to appear earlier
- Still room for improvement (perfect = 1.0)

---

## Performance by Query Type

| Query Type | Count | P@5 | R@5 | MRR | Notes |
|------------|-------|-----|-----|-----|-------|
| **Factual** | 17 | 0.294 | 1.000 | 0.676 | Best performing category |
| **How-To** | 22 | 0.245 | 0.909 | 0.575 | Most common, moderate performance |
| **Comparison** | 5 | 0.240 | 1.000 | 0.767 | High MRR, good ranking |
| **Troubleshooting** | 11 | 0.218 | 0.909 | 0.715 | Lowest precision |

### Observations

1. **Factual queries perform best** (P@5 = 0.294)
   - Likely due to clearer keyword matching
   - Example: "What is semantic search?" - clear terms

2. **Troubleshooting queries perform worst** (P@5 = 0.218)
   - Problem descriptions use different vocabulary than solutions
   - Example: "Context list is too long" vs "how to delete contexts"

3. **Comparison queries have highest MRR** (0.767)
   - Relevant docs appear early despite low precision
   - Specific comparative terms ("vs", "difference") help ranking

4. **How-to queries are most common** (40% of test set)
   - Middle-of-the-road performance
   - Critical category to improve for user experience

---

## Query Success Analysis

| Success Level | Count | Percentage | Description |
|---------------|-------|------------|-------------|
| **Perfect (P@5 = 1.0)** | 0 | 0.0% | All top-5 results relevant |
| **Partial (0 < P@5 < 1)** | 52 | 94.5% | Some relevant, some not |
| **Failed (P@5 = 0)** | 3 | 5.5% | No relevant results in top-5 |

### Key Finding

**No perfect queries** - Even best-performing queries include irrelevant results. This indicates systematic precision issues that semantic search should address.

**Very few complete failures** (5.5%) - Substring search rarely misses entirely, suggesting high recall is already achieved.

---

## Top 10 Best Performing Queries

| Rank | Query | P@5 | Type | Analysis |
|------|-------|-----|------|----------|
| 1 | How do I set up context management for my project? | 0.40 | how-to | Good keyword overlap ("context management") |
| 2 | What is semantic search and why do we need it? | 0.40 | factual | Clear technical term ("semantic search") |
| 3 | How do I fetch contexts at the start of a session? | 0.40 | how-to | Specific action words ("fetch", "contexts") |
| 4 | When should I update the decision log? | 0.40 | how-to | Clear entities ("decision log") |
| 5 | What are the constraints for the semantic search implementation? | 0.40 | factual | Multiple good keywords |
| 6 | What is the MVP scope for semantic search? | 0.40 | factual | Specific terms ("MVP", "semantic search") |
| 7 | What are the scientist's action items? | 0.40 | factual | Clear role + task terms |
| 8 | What are the acceptance criteria for the MVP? | 0.40 | how-to | Specific technical terms |
| 9 | What transport does the MCP server use? | 0.40 | troubleshooting | Unique technical term ("transport") |
| 10 | What is the target improvement for semantic search? | 0.40 | factual | Clear metric-related keywords |

### Pattern: Best Queries Have

1. **Unique technical terms** - "semantic search", "MVP", "transport"
2. **Clear entity names** - "decision log", "MCP server"
3. **Specific action words** - "fetch", "update", "implement"
4. **Multiple relevant keywords** - increasing chance of matches

---

## Top 10 Worst Performing Queries

| Rank | Query | P@5 | Type | Problem |
|------|-------|-----|------|---------|
| 46-48 | (Multiple queries) | 0.20 | various | Generic terms match too broadly |
| 49 | How do I validate that contexts match reality? | 0.00 | how-to | Abstract concept ("reality"), no keyword match |
| 50 | How do I search for contexts by topic? | 0.00 | how-to | Meta-query about search itself |
| 51 | Test set shows contexts are severely outdated - how to recover? | 0.00 | troubleshooting | Long problem description, no matching solution vocabulary |

### Pattern: Worst Queries Have

1. **Abstract concepts** - "reality", "match reality", "validate"
2. **Meta-queries** - Asking about the system's own capabilities
3. **Long problem descriptions** - Too specific, no exact phrase matches
4. **Symptom-solution vocabulary mismatch** - Problem uses different words than solution

---

## Common Failure Modes

### 1. Vocabulary Mismatch (Semantic Gap)

**Example:**
- Query: "How do I validate that contexts match reality?"
- Issue: Documents discuss "checking staleness" and "verifying consistency"
- Miss: No document uses "validate" or "match reality"

**Impact:** Moderate - affects ~20% of queries
**Semantic Search Impact:** **HIGH** - Embeddings would bridge vocabulary differences

---

### 2. Overly Broad Matches

**Example:**
- Query: "What is the next action to take?"
- Issue: Word "action" appears in many contexts (action items, workflows)
- Result: Returns all contexts, precision suffers

**Impact:** High - affects ~40% of queries
**Semantic Search Impact:** **HIGH** - Better understanding of query intent

---

### 3. Missing Specificity

**Example:**
- Query: "Which contexts should I always fetch at session start?"
- Issue: Documents mention "fetching contexts" and "session start" separately
- Result: Returns many contexts that mention either term

**Impact:** Moderate - affects ~30% of queries
**Semantic Search Impact:** **MEDIUM** - Can better combine multi-part queries

---

### 4. Long-Tail / Meta Queries

**Example:**
- Query: "Test set shows contexts are severely outdated - how to recover?"
- Issue: Very specific scenario, no exact phrase match
- Result: Misses relevant "staleness recovery" documentation

**Impact:** Low - affects ~10% of queries
**Semantic Search Impact:** **HIGH** - Can match conceptually similar content

---

## Baseline Strengths

Despite limitations, substring search has notable strengths:

### 1. Exact Technical Term Matching

✅ Queries with unique technical terms perform well  
✅ Example: "semantic search", "MVP", "STDIO transport"  
✅ Benefit: Clear, unambiguous terms lead to good matches

### 2. High Recall

✅ Rarely misses relevant documents entirely (94.5% recall)  
✅ Benefit: Users can find what they need (if willing to search results)

### 3. Simple and Fast

✅ No model loading or embedding generation  
✅ Benefit: Low latency, simple implementation

---

## Implications for Semantic Search

### Expected Improvements

Based on failure mode analysis, semantic search should improve:

1. **Precision (PRIMARY GOAL)**
   - Target: P@5 > 0.33 (30% improvement from 0.255)
   - How: Better understanding of query intent, less noise

2. **Vocabulary Matching**
   - Target: Reduce vocabulary mismatch failures from 20% to <5%
   - How: Embeddings capture synonyms and paraphrases

3. **Query Intent Understanding**
   - Target: Improve performance on complex multi-part queries
   - How: Embeddings understand relationships between concepts

4. **Ranking Quality**
   - Target: MRR > 0.85 (30% improvement from 0.652)
   - How: Similarity scores provide better ranking

### Areas Where Improvement May Be Limited

1. **Recall** - Already 94.5%, little room for improvement
2. **Exact term matches** - Semantic search may not improve much on queries that already work well
3. **Very rare/unique scenarios** - Embeddings need examples to generalize

---

## Target Metrics for Semantic Search

Based on baseline performance and 30% improvement target:

| Metric | Baseline | Target (+30%) | Stretch Goal |
|--------|----------|---------------|--------------|
| **Precision@5** | 0.255 | **≥ 0.332** | 0.400 |
| **Recall@5** | 0.945 | 0.945 (maintain) | 1.000 |
| **MRR** | 0.652 | **≥ 0.848** | 0.900 |
| **NDCG@10** | 0.742 | **≥ 0.965** | 1.000 |

**Primary Acceptance Criterion:** Precision@5 ≥ 0.332 (30% relative improvement)  
**Statistical Significance:** p < 0.05 via paired t-test

---

## Recommendations

### For Semantic Search Implementation

1. **Focus on precision improvement** - This is where gains will be clearest
2. **Maintain high recall** - Don't trade recall for precision
3. **Prioritize how-to and troubleshooting queries** - Highest impact categories
4. **Test on queries with vocabulary mismatch** - Key differentiator

### For Evaluation (Action Item 03)

1. **Run paired t-test** on per-query improvements
2. **Analyze failure mode reduction** - How many vocabulary mismatches resolved?
3. **Check for regressions** - Ensure exact-match queries don't degrade
4. **Per-category analysis** - Which query types improve most?

### If Target Not Met

**If P@5 improvement < 30%:**
- Analyze which queries improved vs regressed
- Check embedding quality (are similar concepts clustered?)
- Consider hybrid approach (semantic + keyword)
- Document actual improvement and make conditional acceptance case

**If P@5 improvement ≥ 20% but < 30%:**
- Strong candidate for conditional acceptance
- 20-30% improvement is still substantial value
- Recommend acceptance with Phase 2 hybrid search

---

## Data Quality Notes

### Test Set Characteristics

- 55 queries across 4 categories
- 6 contexts in corpus (small but realistic for MVP)
- Average 1.33 relevant contexts per query
- No queries with zero relevant contexts

### Evaluation Method

**Word-Based Substring Search:**
- Tokenizes query into words
- Filters stop words (a, the, is, etc.)
- Searches for documents containing any query words
- Ranks by percentage of query words matched

**Why Not Pure Substring?**
- Pure substring matching (exact phrase) had 0.000 metrics
- Not realistic comparison - even basic search does word tokenization
- Word-based approach is fairer baseline

---

## Conclusion

The baseline substring search achieves **moderate but improvable performance**:

- ✅ High recall ensures users can find information
- ❌ Low precision creates friction (too many irrelevant results)
- ✅ Moderate ranking means relevant docs appear reasonably early
- ⚠️ Vocabulary gaps and broad matching are key weaknesses

**Semantic search has clear opportunity to improve precision and ranking** while maintaining the baseline's high recall. The 30% improvement target is achievable and will provide substantial user experience gains.

**Next Steps:**
1. Developer implements semantic search MVP
2. Run Action Item 03 (Semantic Search Evaluation) using same test set
3. Compare results with statistical significance testing
4. Make MVP acceptance decision based on results

---

**Files:**
- Results: `baseline-results.json` (full per-query data)
- Test Set: `evaluation-testset.json` (55 queries)
- Evaluation Script: `evaluate.py` (reusable for semantic evaluation)

**Last Updated:** 2024-12-16

