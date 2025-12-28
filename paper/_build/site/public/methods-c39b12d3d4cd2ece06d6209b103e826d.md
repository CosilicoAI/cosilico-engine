# Methods

## System Architecture

Our system comprises five components:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Statute   │────▶│   Claude    │────▶│  Generated  │
│    Text     │     │   Agent     │     │    Code     │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                    │
                           │    ┌───────────────┘
                           │    │
                    ┌──────▼────▼──────┐
                    │     Executor     │
                    │   (DSL Parser)   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   Test Cases     │
                    │  (from Oracles)  │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │     Scorer       │
                    │  (Accuracy, MAE) │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │    Diagnoser     │──────▶ Feedback to Agent
                    │ (Failure Analysis)│
                    └──────────────────┘
```

### Claude Agent

We use Claude Sonnet 4 with tool use. The agent has access to two tools:

1. **execute_dsl**: Runs generated code against test cases, returns accuracy and failure details
2. **submit_final_code**: Signals completion with final implementation

The system prompt provides:
- DSL specification (entity types, formula syntax, reference format)
- Available parameters (rates, thresholds from IRS publications)
- Instructions for iteration

### Domain-Specific Language

Our Cosilico DSL captures:
- **Variables**: Named calculations with entity scope (Person, TaxUnit, Household)
- **Formulas**: Arithmetic expressions with conditionals and functions
- **References**: Pointers to other variables and parameters
- **Citations**: Links to statutory sections

Example:
```
variable eitc_phase_in_credit:
  entity: TaxUnit
  period: Year
  dtype: Money
  citation: "26 USC § 32(a)(1)"

  references:
    earned_income: us/irs/income/earned_income
    phase_in_rate: param.irs.eitc.phase_in_rate

  formula:
    min(earned_income, earned_income_amount) * phase_in_rate
```

### Oracles (Blackbox Only)

Critically, the agent has **no access to oracle source code**—only output comparisons. This prevents trivial copying and ensures the agent must learn statutory logic from the text itself.

**PolicyEngine-US** serves as primary oracle:
- Comprehensive federal tax implementation
- Validated against IRS examples
- API access for automated testing
- Agent sees only: (input, expected_output) pairs

**TAXSIM** (NBER) provides secondary validation:
- Independent implementation
- Flags disagreements for investigation
- Cross-oracle agreement increases confidence

### Hard Constraints vs. Soft Rewards

We distinguish between **hard constraints** (binary pass/fail) and **soft rewards** (continuous optimization targets):

**Hard Constraints** (must pass, not in reward function):
| Constraint | Enforcement | Rationale |
|------------|-------------|-----------|
| No hardcoded values | CI linter: only 0, 1, -1 allowed in formulas | Forces parameterization |
| Inline tests pass | DSL executor validates | Catches syntax and basic logic errors |
| Valid DSL syntax | Parser rejects invalid code | Agent must produce parseable output |
| Entity/period consistency | Type checker | Prevents dimensional errors |

**Soft Rewards** (continuous, optimized via RL):
| Reward Component | Weight | Metric |
|------------------|--------|--------|
| Oracle alignment | 0.60 | 1 - MAE/max_value across test cases |
| Token efficiency | 0.15 | 1 - (tokens_used / max_tokens) |
| Performance | 0.15 | Log-scale execution time (vectorized) |
| Generalization | 0.10 | Holdout accuracy on unseen cases |

Token efficiency rewards concise encodings and fast convergence—fewer iterations = fewer tokens = higher reward.

This separation ensures that failing a hard constraint is not a "low reward" but a rejection—the agent must retry until constraints pass. The soft rewards then guide toward optimal solutions among valid candidates.

### Hyperparameters

Beyond model choice, key hyperparameters affect convergence:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Max iterations | 10 | Hard cap on encode-validate cycles |
| Target accuracy | 0.95 | Early stop if achieved |
| Batch size | 50 | Test cases per validation round |
| Feedback limit | 10 | Max failing cases shown to agent |
| Temperature | 0.0 | Deterministic generation |

**Batch size** trades off signal vs. cost: larger batches catch more errors per iteration but increase API calls. We found 50 cases per round balances convergence speed with cost, increasing to 200 for aggregate microsim validation.

**Feedback limit** prevents prompt overflow—showing 10 representative failures is sufficient for diagnosis.

### Test Case Generation

For each provision, we generate test cases covering:
- Income distribution (log-uniform from $0 to $1M)
- Family structures (0-4 children, various filing statuses)
- Boundary values (exactly at thresholds)
- Edge cases (zero income, maximum values)

Typical test suite: 100-500 cases per provision.

## Pilot Phase Learnings

Before the formal experiment, we conducted pilot encoding runs on select provisions to validate our infrastructure and refine the experimental design. These runs are not included in the main results but informed key methodological choices.

### Key Discovery: Phase-In vs Phase-Out Rate Confusion

During pilot encoding of the Earned Income Tax Credit, we discovered a subtle bug pattern. The EITC has **different rates** for phase-in (34% for 1 child) and phase-out (15.98% for 1 child), but the agent initially used the phase-out rate for both regions—producing a systematic $9.2B aggregate underestimate vs PolicyEngine.

This error was only caught by **record-by-record comparison** across the full CPS microdata (200K+ records), not by unit test cases. The fix was straightforward once identified:

```diff
- phase_in_credit = earned_income * phaseout_rate  # WRONG
+ phase_in_credit = earned_income * phase_in_rate  # CORRECT
```

**Implications for experiment design:**
1. Validation must include aggregate microsimulation, not just unit tests
2. Parameters with similar names (phase_in_rate vs phaseout_rate) are high-confusion risk
3. The agent benefits from explicit rate derivation checks in feedback

### Infrastructure Validated

- **Encoder RL loop**: Converged to 100% accuracy on standard deduction within 3 iterations
- **Validator integration**: PolicyEngine API successfully returns test case results
- **No-hardcodes linter**: Correctly rejects formulas like `if age >= 65` (must use parameters)
- **Experiment tracking**: Run metadata saved to `optimization/runs/`

## Provision Selection

We encode 15 provisions from the Internal Revenue Code, stratified by complexity:

| Phase | Provisions | Complexity | Examples |
|-------|-----------|------------|----------|
| 1 | 5 | Simple (1-3) | EITC phase-in, Standard deduction |
| 2 | 5 | Medium (4-6) | Full EITC, Child care credit |
| 3 | 5 | Complex (7+) | AMT, NIIT, QBI deduction |

Complexity score = conditionals + parameters + references + 2×nesting

## Metrics

**Primary:**
- **Accuracy**: Proportion of test cases passing (within $1 tolerance)
- **Iterations**: Generate-test cycles to reach 95%
- **Tokens**: API usage (input + output)
- **Cost**: Tokens × rate ($3/M input, $15/M output for Sonnet)

**Secondary:**
- Time to convergence
- Error type distribution
- Human interventions required

## Analysis Plan

All hypotheses preregistered (see Appendix A):

- **H1 (Convergence)**: Bootstrap CI for convergence rate
- **H2 (Complexity)**: Regression of iterations on complexity score
- **H3 (Transfer)**: Paired comparison of early vs. late provisions
- **H4 (Cost)**: Trend analysis and comparison to manual estimates
- **H5 (Failures)**: Chi-square test for failure category distribution
