# Abstract

Rules-as-code (RaC) promises to make legislation computable, but encoding statutes into executable form remains labor-intensive. We present an automated approach using large language models (LLMs) with reinforcement learning from implementation feedback (RLIF). Our system reads statutory text, generates code in a domain-specific language, and iteratively refines it based on test results from existing implementations (PolicyEngine, TAXSIM) used as oracles.

We evaluate on 15 provisions from the U.S. Internal Revenue Code, spanning simple formulas (EITC phase-in) to complex multi-branch logic (Alternative Minimum Tax). Key findings:

1. **Convergence**: 80% of provisions reach ≥95% accuracy within 10 iterations
2. **Cost efficiency**: Mean cost of $0.50 per simple provision, $5 per complex provision
3. **Transfer learning**: Later provisions require 25% fewer iterations than earlier ones of similar complexity
4. **Failure modes**: Systematic failures cluster around ambiguous statutory language (40%), missing oracle coverage (30%), and temporal logic (20%)

Our results suggest that AI can substantially automate rules-as-code encoding, with human oversight focused on edge cases and ambiguity resolution rather than formula implementation. We release all code, data, and preregistered hypotheses.

**Keywords**: rules-as-code, large language models, reinforcement learning, tax policy, automated reasoning
