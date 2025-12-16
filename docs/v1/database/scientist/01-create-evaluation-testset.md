# Scientist Action Item 01: Create Evaluation Test Set

**Status:** 🔴 Not Started  
**Priority:** HIGH - BLOCKING for quality validation  
**Owner:** ML Scientist  
**Estimated Time:** 4-6 hours  
**Dependencies:** None (can start immediately)

---

## Objective

Create a comprehensive evaluation test set with 50+ queries and relevance judgments to measure semantic search quality against the baseline substring search.

**Why This Matters:** Without a test set, we cannot claim "measurable improvement" - we'd be deploying without validation.

---

## Requirements Reference

From requirements.md Section 7.2 (RT-10):

**Specifications:**
- **Size:** Minimum 50 queries
- **Coverage:** Representative of actual LLM usage patterns
- **Relevance Judgments:** Binary (relevant/not relevant) per query-context pair
- **Diversity:** Include various query types

---

## Deliverables

### 1. Test Set File

**Location:** `docs/v1/database/scientist/evaluation-testset.json`

**Format:**
```json
{
  "metadata": {
    "version": "1.0.0",
    "created_date": "YYYY-MM-DD",
    "num_queries": 50,
    "description": "Evaluation test set for semantic search quality validation"
  },
  "queries": [
    {
      "id": "q001",
      "query": "How do I train a neural network?",
      "type": "how-to",
      "relevant_contexts": ["ml-basics", "training-guide"],
      "notes": "Broad conceptual query"
    },
    {
      "id": "q002",
      "query": "What is backpropagation?",
      "type": "factual",
      "relevant_contexts": ["ml-basics"],
      "notes": "Specific term definition"
    }
  ]
}
```

### 2. Documentation

**Location:** `docs/v1/database/scientist/evaluation-testset-methodology.md`

Document:
- Query selection methodology
- Relevance judgment criteria
- Query type distribution
- Coverage analysis
- Limitations and biases

---

## Methodology

### Step 1: Query Collection (1-2 hours)

**Sources:**
1. **Actual Usage Logs** (if available)
   - Review recent queries to MCP server
   - Extract common patterns

2. **Anticipated Use Cases**
   - Code questions: "how to implement X"
   - Concept queries: "what is Y"
   - Troubleshooting: "error when doing Z"
   - Comparison: "difference between A and B"

3. **Edge Cases**
   - Very short queries (1-2 words)
   - Very long queries (multiple sentences)
   - Queries with typos or variations
   - Queries with rare technical terms

**Target Distribution:**
- 40% how-to questions
- 30% factual/definition queries
- 20% troubleshooting queries
- 10% comparison/analysis queries

### Step 2: Relevance Judgments (2-3 hours)

For each query, identify relevant contexts:

**Criteria for "Relevant":**
- ✅ Context directly answers the query
- ✅ Context provides necessary background information
- ✅ Context includes the answer as part of larger discussion

**Criteria for "Not Relevant":**
- ❌ Context only tangentially related
- ❌ Context mentions query terms but doesn't help answer
- ❌ Context is about different topic despite keyword overlap

**Process:**
1. Read query
2. Manually search through .mdc files
3. Mark all relevant contexts
4. Aim for 2-5 relevant contexts per query (some may have 1, others 10+)

### Step 3: Quality Check (1 hour)

**Validation:**
- [ ] All 50+ queries have at least 1 relevant context
- [ ] Query types are diverse (not all "how-to")
- [ ] Relevance judgments are consistent
- [ ] No obvious queries missing (coverage check)
- [ ] Edge cases included (short, long, typos, rare terms)

**Peer Review (Optional but Recommended):**
- Have developer or colleague review 10 sample queries
- Check if relevance judgments seem reasonable
- Adjust based on feedback

---

## Query Type Categories

### Category 1: How-To Queries (40%)

**Examples:**
- "How do I configure the database?"
- "Steps to implement authentication"
- "Best way to handle errors"

**Characteristics:** Procedural, action-oriented, often multi-step

---

### Category 2: Factual/Definition Queries (30%)

**Examples:**
- "What is JWT authentication?"
- "Define REST API"
- "Explain event loop"

**Characteristics:** Conceptual, definitional, often single concept

---

### Category 3: Troubleshooting Queries (20%)

**Examples:**
- "Why is my API returning 500?"
- "Error: connection refused"
- "Database not updating"

**Characteristics:** Problem-focused, often includes error messages or symptoms

---

### Category 4: Comparison/Analysis Queries (10%)

**Examples:**
- "Difference between REST and GraphQL"
- "When to use Redis vs PostgreSQL"
- "Pros and cons of microservices"

**Characteristics:** Comparative, analytical, requires synthesis

---

## Success Criteria

- [ ] Test set has 50+ queries
- [ ] All queries have relevance judgments
- [ ] Query types are distributed as specified
- [ ] Documentation explains methodology
- [ ] Test set validated (self-review + optional peer review)
- [ ] File committed to repository

---

## Next Steps After Completion

1. **Baseline Evaluation** (Action Item 02)
   - Run current substring search against test set
   - Measure Precision@5, Recall@5, MRR
   - Document baseline metrics

2. **Block Until Developer Implements Semantic Search**
   - Wait for MVP implementation
   - Coordinate with developer on integration testing

3. **Semantic Search Evaluation** (Action Item 03)
   - Run semantic search against same test set
   - Compare to baseline
   - Report results with statistical significance

---

## Tips and Best Practices

### Creating Good Test Queries

**DO:**
- ✅ Use natural language (how users would actually ask)
- ✅ Include variations (synonyms, different phrasings)
- ✅ Cover different difficulty levels
- ✅ Include queries that baseline handles well (to detect regressions)

**DON'T:**
- ❌ Craft queries to favor semantic search (introduces bias)
- ❌ Only include queries where baseline fails (unbalanced)
- ❌ Use technical jargon unless that's how users query
- ❌ Make relevance judgments too strict (if somewhat relevant, include it)

### Handling Ambiguous Relevance

Some contexts are borderline relevant. Guidelines:

- **Clearly Relevant:** Include (judgment = 1)
- **Clearly Not Relevant:** Exclude (judgment = 0)
- **Borderline:** Include with note (judgment = 1, note = "borderline")

During evaluation, can analyze borderline cases separately.

---

## Example Query (Fully Annotated)

```json
{
  "id": "q042",
  "query": "How do I implement OAuth2 authentication?",
  "type": "how-to",
  "tokens": 7,
  "difficulty": "medium",
  "relevant_contexts": [
    "auth-oauth2-guide",
    "api-security-overview",
    "user-authentication-patterns"
  ],
  "borderline_contexts": [
    "jwt-tokens-explained"
  ],
  "not_relevant_but_mention_keywords": [
    "database-authentication"
  ],
  "notes": "OAuth2 is complex, multiple relevant contexts expected. JWT is borderline because it's related but not OAuth2-specific.",
  "expected_baseline_performance": "poor",
  "rationale": "Baseline will match 'authentication' but may miss OAuth2-specific guidance due to lack of exact term matching"
}
```

---

## Time Tracking

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| Query Collection | 1-2h | | |
| Relevance Judgments | 2-3h | | |
| Quality Check | 1h | | |
| Documentation | 0.5h | | |
| **Total** | **4.5-6.5h** | | |

---

## Completion Checklist

- [ ] Test set JSON file created with 50+ queries
- [ ] All queries have relevance judgments
- [ ] Query type distribution verified
- [ ] Methodology documentation written
- [ ] Self-review completed
- [ ] (Optional) Peer review completed
- [ ] Files committed to repository
- [ ] Ready for Action Item 02 (Baseline Evaluation)

---

**Status Update Procedure:**
When complete, update status to: 🟢 Complete  
Link to: `evaluation-testset.json` and `evaluation-testset-methodology.md`

