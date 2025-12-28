# Introduction

## The Rules-as-Code Challenge

Legislation governs trillions of dollars in tax collection and benefit distribution, yet remains encoded primarily in natural language. Converting statutes to executable code—rules-as-code (RaC)—enables:

- **Simulation**: Model policy changes before enactment
- **Automation**: Streamline benefit delivery and tax filing
- **Transparency**: Make calculations auditable and reproducible
- **Accessibility**: Let citizens understand how rules affect them

But encoding is expensive. A single tax provision can take days of expert effort, and the full U.S. tax code contains thousands of interacting rules. Organizations like PolicyEngine and NBER's TAXSIM have encoded major provisions, but coverage remains incomplete and maintenance is ongoing.

## AI as Encoder

Recent advances in large language models (LLMs) suggest a different approach: rather than humans reading statute and writing code, have AI do both. The key insight is that existing implementations can serve as **oracles**—ground truth for training.

This is analogous to reinforcement learning from human feedback (RLHF), but with deterministic feedback from code execution:

1. AI reads statutory text
2. AI generates code
3. Code runs against test cases derived from oracles
4. Accuracy signal trains the AI to improve

We call this **reinforcement learning from implementation feedback (RLIF)**.

## Contributions

This paper makes three contributions:

1. **System**: We implement an agentic loop that encodes statutory provisions using Claude with tool use, achieving high accuracy on real tax provisions.

2. **Empirical evaluation**: We test on 15 IRC provisions with preregistered hypotheses, measuring convergence rates, costs, and transfer learning effects.

3. **Failure analysis**: We categorize systematic failure modes, informing where human oversight is most needed.

## Roadmap

- **Methods**: System architecture, provision selection, metrics
- **Results**: Accuracy, cost, transfer learning, failure modes
- **Discussion**: Implications for RaC, limitations, future work
- **Appendices**: Full preregistration, provision details, code listings
