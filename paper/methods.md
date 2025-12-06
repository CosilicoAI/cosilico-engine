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

### Oracles

**PolicyEngine-US** serves as primary oracle:
- Comprehensive federal tax implementation
- Validated against IRS examples
- API access for automated testing

**TAXSIM** (NBER) provides secondary validation:
- Independent implementation
- Flags disagreements for investigation

### Test Case Generation

For each provision, we generate test cases covering:
- Income distribution (log-uniform from $0 to $1M)
- Family structures (0-4 children, various filing statuses)
- Boundary values (exactly at thresholds)
- Edge cases (zero income, maximum values)

Typical test suite: 100-500 cases per provision.

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
