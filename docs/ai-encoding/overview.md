# AI Rules Engine

Cosilico is building AI that reads legislation and writes executable code.

## The Vision

We're training AI agents to encode law directly from statutory text. Not translating from existing implementations. Not assisting human engineers. **Reading law and producing code.**

```
┌─────────────────┐                              ┌─────────────────┐
│  26 USC § 32    │                              │  Executable     │
│                 │────────▶  AI Agent  ────────▶│  Cosilico DSL   │
│  (EITC statute) │                              │                 │
└─────────────────┘                              └─────────────────┘
```

Existing implementations like PolicyEngine and TAXSIM become **verification oracles** - they provide the reward signal that trains the AI, not the source to translate from.

## Why This Is Different

**Traditional approach:** Lawyers read statute → Engineers write code → QA validates

**Our approach:** AI reads statute → AI writes code → Oracles validate → AI improves

The human role shifts from implementation to oversight. We review edge cases, resolve oracle disagreements, and validate ambiguous interpretations - not write formulas.

## How It Works

### 1. Statute In, Code Out

The AI agent receives:
- Raw statutory text (26 USC § 32, California Revenue and Taxation Code, etc.)
- The target DSL specification
- Existing encoded rules as context

It produces executable Cosilico DSL code organized by statutory citation.

### 2. Oracles as Reward Function

PolicyEngine, TAXSIM, and other implementations have already encoded tax law. They may disagree on edge cases, but they agree on the vast majority of scenarios.

We use them as **ground truth**:
- Generate thousands of test households
- Run through oracles to get expected outputs
- Score AI-generated code against oracle outputs
- Iterate until convergence

This is **reinforcement learning from implementation feedback** - similar to RLHF, but with deterministic reward signals from code execution rather than human preferences.

### 3. Iterative Refinement

This is not one-shot generation. The agent iterates:

```python
for iteration in range(max_iterations):
    # Generate or revise code
    code = agent.generate(statute, context, failures)

    # Test against oracles
    reward = evaluate(code, test_cases, oracles)

    if reward >= 0.99:
        return code  # Success

    # Diagnose failures for next iteration
    failures = diagnose(code, test_cases)
```

Each iteration improves based on structured failure feedback.

### 4. Human Oversight

Humans handle what AI can't:

- **Oracle disagreements** - When PolicyEngine and TAXSIM disagree, which is right? Often neither - the disagreement surfaces a genuine ambiguity in statute.
- **Edge case validation** - Novel scenarios with no oracle coverage
- **Policy judgment** - When statute is genuinely ambiguous, legal interpretation is required
- **Override mechanism** - Humans can correct AI outputs, and those corrections feed back into training

## The Training Data Factory

The moat isn't the encoded rules - those are open source. The moat is:

1. **The oracle stack** - Unified interface to PolicyEngine, TAXSIM, IRS examples, state calculators
2. **The test case generator** - Boundary cases, edge cases, adversarial scenarios
3. **The curriculum** - Progressive complexity from simple deductions to full tax liability
4. **The feedback loop** - Every human correction improves the system

Each jurisdiction we encode makes the next one faster. Each edge case we resolve trains better judgment.

## Scaling Path

### Phase 1: US Federal Tax
Train on IRC. PolicyEngine-US and TAXSIM provide dense oracle coverage.

### Phase 2: US States
Transfer learning from federal. Most states couple to federal AGI - the agent already knows that structure.

### Phase 3: Benefits Programs
SNAP, Medicaid, housing assistance. PolicyEngine covers these; expand oracle stack as needed.

### Phase 4: International
UK (PolicyEngine-UK as oracle), Canada, EU jurisdictions. Transfer learning across legal systems.

### Phase 5: New Legislation
When Congress passes new law, no oracle exists. The agent:
- Uses similar existing rules as templates
- Extracts examples from legislative text
- Generates with lower confidence
- Flags for human review

Over time, confidence on new legislation increases as the agent learns statutory patterns.

## What We're Building

An AI system that:
- Reads any tax or benefit statute
- Produces executable, auditable code
- Validates against multiple independent implementations
- Improves continuously from human oversight
- Scales across jurisdictions and legal domains

This is computational law at scale.
