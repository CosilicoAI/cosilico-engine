# Results

```{note}
Results will be populated as experiments are run. This section shows the planned structure and preliminary findings.
```

## Preliminary Results

### EITC Phase-In (Simple Provision)

**Configuration:**
- Statute: 26 USC § 32(a)(1)
- Test cases: 36
- Target accuracy: 95%

**Result:**
- Accuracy: 100%
- Iterations: 1
- Tokens: 4,491
- Cost: $0.023

The agent correctly encoded the phase-in formula on the first attempt:

```
formula:
  min(earned_income, earned_income_amount[n_qualifying_children])
    * phase_in_rate[n_qualifying_children]
```

### Full EITC with Phase-Out (Medium Provision)

**Configuration:**
- Statute: 26 USC § 32 (full)
- Test cases: 104
- Target accuracy: 85%

**Result:**
- Accuracy: 100%
- Iterations: 6
- Cost: ~$0.15

The agent required multiple iterations to handle the phase-out logic:

| Iteration | Accuracy | Issue |
|-----------|----------|-------|
| 1 | 0% | Syntax error in multi-line formula |
| 2 | 0% | Runtime error in expression |
| 3 | 49% | Missing phase-out calculation |
| 4 | 0% | Syntax error in conditional |
| 5 | 0% | Incorrect threshold reference |
| 6 | 100% | Correct implementation |

## Full Study Results

*To be completed after running all 15 provisions*

### H1: Convergence Rate

| Complexity | Provisions | Converged (≤10 iter) | Rate |
|------------|-----------|---------------------|------|
| Simple | 5 | TBD | TBD |
| Medium | 5 | TBD | TBD |
| Complex | 5 | TBD | TBD |
| **Total** | **15** | TBD | TBD |

### H2: Complexity Scaling

```{code-cell} python
:tags: [hide-input]
# Placeholder for regression analysis
# iterations ~ complexity_score
```

### H3: Transfer Learning

| Provision Set | Mean Iterations | Std |
|--------------|----------------|-----|
| First 5 | TBD | TBD |
| Last 5 | TBD | TBD |
| Difference | TBD | - |

### H4: Cost Analysis

| Complexity | Mean Cost | Range |
|------------|-----------|-------|
| Simple | TBD | TBD |
| Medium | TBD | TBD |
| Complex | TBD | TBD |

### H5: Failure Modes

| Category | Count | Proportion |
|----------|-------|------------|
| Ambiguous statute | TBD | TBD |
| Missing oracle | TBD | TBD |
| Oracle disagreement | TBD | TBD |
| Temporal logic | TBD | TBD |
| Other | TBD | TBD |
