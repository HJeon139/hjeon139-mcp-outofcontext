# Scientist Action Item 02: Baseline Evaluation

**Status:** 🟡 Blocked (waiting for Action Item 01)  
**Priority:** HIGH - Required before semantic search comparison  
**Owner:** ML Scientist  
**Estimated Time:** 2-3 hours  
**Dependencies:** 
- ✅ Action Item 01 (evaluation test set) must be complete
- ✅ Current substring search must be functional

---

## Objective

Measure baseline performance of the current substring search against the evaluation test set to establish comparison metrics for semantic search.

**Why This Matters:** We need a baseline to claim "improvement." Without baseline metrics, we can't validate the 30% improvement target.

---

## Deliverables

### 1. Baseline Results

**Location:** `docs/v1/database/scientist/baseline-results.json`

**Format:**
```json
{
  "metadata": {
    "evaluation_date": "YYYY-MM-DD",
    "search_method": "substring",
    "test_set_version": "1.0.0",
    "num_queries": 50,
    "system_info": {
      "num_contexts": 1234,
      "mcp_server_version": "1.0.1"
    }
  },
  "metrics": {
    "precision_at_5": 0.42,
    "recall_at_5": 0.38,
    "mrr": 0.51,
    "ndcg_at_10": 0.45
  },
  "per_query_results": [
    {
      "query_id": "q001",
      "query": "How do I train a neural network?",
      "top_5_results": ["context-3", "context-12", ...],
      "relevant_retrieved": 2,
      "relevant_total": 3,
      "precision_at_5": 0.4,
      "recall_at_5": 0.67,
      "reciprocal_rank": 0.5
    }
  ]
}
```

### 2. Analysis Report

**Location:** `docs/v1/database/scientist/baseline-analysis.md`

Document:
- Overall metrics interpretation
- Where baseline performs well
- Where baseline fails
- Common failure modes
- Insights for improvement

---

## Methodology

### Step 1: Setup Evaluation Environment (30 min)

**Script Location:** `docs/v1/database/scientist/evaluate.py`

Create Python script to:
1. Load test set from `evaluation-testset.json`
2. Query current MCP server `search_context` tool
3. Calculate metrics for each query
4. Aggregate overall metrics
5. Save results to JSON

**Dependencies:**
```bash
pip install numpy scikit-learn
```

### Step 2: Run Evaluation (30 min)

**Process:**
```bash
# Ensure MCP server is running
cd /path/to/out_of_context

# Run evaluation script
python docs/v1/database/scientist/evaluate.py \
  --testset docs/v1/database/scientist/evaluation-testset.json \
  --output docs/v1/database/scientist/baseline-results.json \
  --search-method substring
```

**What the script does:**
1. For each query in test set:
   - Call `search_context` with query string
   - Get top-10 results
   - Compare against relevant_contexts from test set
   - Calculate metrics

2. Aggregate metrics:
   - Precision@5 = Average across all queries
   - Recall@5 = Average across all queries
   - MRR = Average reciprocal rank of first relevant result
   - NDCG@10 = Normalized discounted cumulative gain

### Step 3: Analyze Results (1-2 hours)

**Questions to Answer:**

1. **Overall Performance**
   - What are the baseline metrics?
   - Are they better or worse than expected?

2. **Performance by Query Type**
   - How-to queries: P@5 = ?
   - Factual queries: P@5 = ?
   - Troubleshooting: P@5 = ?
   - Comparison: P@5 = ?

3. **Failure Mode Analysis**
   - What types of queries fail completely (no relevant results)?
   - What types of queries get partially correct results?
   - Common patterns in failures?

4. **Baseline Strengths**
   - Where does substring search perform well?
   - Queries with exact keyword matches
   - Queries with unique terms

**Analysis Template:**

```markdown
## Baseline Performance Analysis

### Overall Metrics
- Precision@5: X.XX
- Recall@5: X.XX  
- MRR: X.XX
- NDCG@10: X.XX

### Performance by Query Type
| Type | Precision@5 | Recall@5 | Count |
|------|-------------|----------|-------|
| How-to | X.XX | X.XX | 20 |
| Factual | X.XX | X.XX | 15 |
| Troubleshooting | X.XX | X.XX | 10 |
| Comparison | X.XX | X.XX | 5 |

### Top 10 Best Performing Queries
[List queries where baseline got P@5 > 0.8]

### Top 10 Worst Performing Queries  
[List queries where baseline got P@5 = 0]

### Common Failure Modes
1. **Synonym Mismatch:** Query uses "neural network", context uses "deep learning"
2. **Partial Match:** Query matches on common term, misses specific intent
3. **No Match:** Query uses paraphrase, no keyword overlap

### Baseline Strengths
1. **Exact Matches:** Queries with unique technical terms
2. **Keyword-Heavy:** Queries with multiple distinct keywords

### Implications for Semantic Search
[What improvements would semantic search provide based on failure modes?]
```

---

## Evaluation Metrics Explained

### Precision@K
**Definition:** Of the top-K results returned, how many are relevant?

**Formula:** `P@K = (# relevant in top-K) / K`

**Example:** Query returns 5 results, 2 are relevant → P@5 = 2/5 = 0.4

**Interpretation:** 
- High P@5 (>0.6): System returns mostly relevant results
- Low P@5 (<0.3): System returns mostly irrelevant results

---

### Recall@K  
**Definition:** Of all relevant contexts, how many appear in top-K?

**Formula:** `R@K = (# relevant in top-K) / (total # relevant)`

**Example:** 3 relevant contexts exist, 2 in top-5 → R@5 = 2/3 = 0.67

**Interpretation:**
- High R@5 (>0.7): System finds most relevant contexts
- Low R@5 (<0.3): System misses many relevant contexts

---

### MRR (Mean Reciprocal Rank)
**Definition:** Average of 1/rank of first relevant result

**Formula:** `MRR = Average(1/rank_of_first_relevant)`

**Example:** 
- Query 1: First relevant at rank 2 → 1/2 = 0.5
- Query 2: First relevant at rank 1 → 1/1 = 1.0
- Query 3: No relevant results → 0.0
- MRR = (0.5 + 1.0 + 0.0) / 3 = 0.5

**Interpretation:**
- High MRR (>0.7): Most queries get relevant result in top positions
- Low MRR (<0.3): Relevant results appear deep in ranking

---

### NDCG@K (Normalized Discounted Cumulative Gain)
**Definition:** Measures ranking quality, considering position

**Formula:** DCG considers both relevance and position (higher positions weighted more)

**Interpretation:**
- NDCG = 1.0: Perfect ranking (all relevant results at top)
- NDCG = 0.0: No relevant results retrieved

---

## Expected Baseline Performance

Based on substring search limitations, expected metrics:

| Metric | Expected Range | Rationale |
|--------|----------------|-----------|
| Precision@5 | 0.3 - 0.5 | Substring matches often return some relevant results but many false positives |
| Recall@5 | 0.2 - 0.4 | Misses contexts with synonyms/paraphrases |
| MRR | 0.4 - 0.6 | When matches occur, often in top results (due to recency sorting) |
| NDCG@10 | 0.3 - 0.5 | Poor ranking due to lack of relevance scoring |

**If baseline is much better than expected:** 
- Substring search may be more effective than assumed
- Test set may favor exact keyword matches
- Review test set for bias

**If baseline is much worse than expected:**
- Good news: More room for improvement
- Semantic search target may be easier to achieve

---

## Success Criteria

- [ ] Evaluation script created and tested
- [ ] Baseline results JSON generated
- [ ] Analysis report written
- [ ] Metrics interpreted correctly
- [ ] Failure modes documented
- [ ] Results reviewed (self + optional peer review)
- [ ] Files committed to repository
- [ ] Ready for comparison when semantic search implemented

---

## Common Issues and Troubleshooting

### Issue: MCP Server Not Responding
**Solution:** Ensure server is running and STDIO transport configured correctly

### Issue: Results Don't Match Test Set
**Solution:** Verify context names in test set match actual .mdc filenames

### Issue: All Metrics are 0.0
**Solution:** Check if relevant_contexts in test set are correct. May need to update test set.

### Issue: Metrics Seem Too High (>0.8)
**Solution:** Test set may be biased toward exact matches. Review query diversity.

---

## Sample Evaluation Script Outline

```python
"""
Baseline evaluation script for substring search.
"""
import json
from pathlib import Path
from typing import Dict, List

def load_testset(path: str) -> Dict:
    """Load evaluation test set."""
    with open(path) as f:
        return json.load(f)

def query_mcp_server(query: str, limit: int = 10) -> List[str]:
    """Query MCP server and return context names."""
    # TODO: Implement actual MCP server query
    # This will depend on how to call search_context
    pass

def calculate_precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """Calculate Precision@K."""
    retrieved_k = retrieved[:k]
    relevant_count = sum(1 for ctx in retrieved_k if ctx in relevant)
    return relevant_count / k if k > 0 else 0.0

def calculate_recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """Calculate Recall@K."""
    if not relevant:
        return 0.0
    retrieved_k = retrieved[:k]
    relevant_count = sum(1 for ctx in retrieved_k if ctx in relevant)
    return relevant_count / len(relevant)

def calculate_reciprocal_rank(retrieved: List[str], relevant: List[str]) -> float:
    """Calculate reciprocal rank of first relevant result."""
    for i, ctx in enumerate(retrieved, 1):
        if ctx in relevant:
            return 1.0 / i
    return 0.0

def evaluate_baseline(testset_path: str, output_path: str):
    """Run baseline evaluation."""
    testset = load_testset(testset_path)
    
    results = {
        "metadata": {...},
        "metrics": {...},
        "per_query_results": []
    }
    
    for query_data in testset["queries"]:
        query = query_data["query"]
        relevant = query_data["relevant_contexts"]
        
        # Query system
        retrieved = query_mcp_server(query, limit=10)
        
        # Calculate metrics
        p5 = calculate_precision_at_k(retrieved, relevant, 5)
        r5 = calculate_recall_at_k(retrieved, relevant, 5)
        rr = calculate_reciprocal_rank(retrieved, relevant)
        
        results["per_query_results"].append({
            "query_id": query_data["id"],
            "query": query,
            "top_5_results": retrieved[:5],
            "precision_at_5": p5,
            "recall_at_5": r5,
            "reciprocal_rank": rr
        })
    
    # Aggregate metrics
    results["metrics"]["precision_at_5"] = sum(r["precision_at_5"] for r in results["per_query_results"]) / len(results["per_query_results"])
    # ... similar for other metrics
    
    # Save results
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    evaluate_baseline(
        "evaluation-testset.json",
        "baseline-results.json"
    )
```

---

## Completion Checklist

- [ ] Evaluation script created
- [ ] Script tested on sample queries
- [ ] Full baseline evaluation run
- [ ] Results JSON saved
- [ ] Analysis report written
- [ ] Metrics interpreted
- [ ] Failure modes documented
- [ ] Files committed to repository
- [ ] Ready for Action Item 03 (when semantic search available)

---

**Status Update Procedure:**
When complete, update status to: 🟢 Complete  
Link to: `baseline-results.json` and `baseline-analysis.md`

