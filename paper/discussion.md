# Discussion

## Key Findings

### AI Can Encode Tax Law

Our preliminary results demonstrate that LLMs can successfully encode statutory provisions into executable code. The EITC phase-in was encoded correctly on the first attempt, and the full EITC (including phase-out) achieved 100% accuracy after 6 iterations.

This suggests that for well-defined provisions with clear formulas, AI encoding is not only possible but efficient—costing cents rather than hours of expert time.

### Iteration Is Key

The full EITC example illustrates the importance of the feedback loop. Initial attempts failed due to syntax errors and incomplete logic. Each iteration provided structured feedback (accuracy, specific failures) that guided the model toward a correct solution.

This is the core of RLIF: the oracle provides a training signal that the model can learn from without human intervention.

### Complexity Matters

We expect (and preliminary data suggests) that complexity correlates with iterations required. Simple provisions converge quickly; complex ones may require more attempts or fail entirely.

The complexity score we defined—counting conditionals, parameters, and references—appears to be a useful predictor. This has practical implications: we can estimate encoding difficulty before starting.

## Implications for Rules-as-Code

### Scaling Potential

If AI can encode provisions at $0.50-$5 each, the economics of RaC change dramatically. The full U.S. tax code could theoretically be encoded for thousands rather than millions of dollars.

More importantly, AI encoding can scale with legislation. As new laws pass, the same system can encode them—potentially faster if transfer learning holds.

### Human Oversight Model

Our failure mode analysis will inform where humans are most needed:

1. **Ambiguous statute**: Legal interpretation beyond AI capability
2. **Missing oracle**: New provisions with no reference implementation
3. **Oracle disagreement**: Conflicting implementations require judgment
4. **Edge cases**: Unusual scenarios not covered by test cases

This suggests a human-in-the-loop model where AI handles routine encoding and humans focus on judgment calls.

### Oracle Dependency

A key limitation: our approach requires oracles. For novel legislation, no oracle exists. We hypothesize that transfer learning will help—the model learns statutory patterns that generalize—but this requires further study.

## Limitations

1. **Oracle quality**: Our accuracy is bounded by oracle accuracy
2. **DSL constraints**: Complex logic may not fit our DSL
3. **Single model**: Results may not generalize to other LLMs
4. **Small sample**: 15 provisions is exploratory, not definitive
5. **Tax-specific**: Other legal domains may differ

## Future Work

1. **Expand provisions**: Test on hundreds of provisions across tax, benefits, regulations
2. **Fine-tuning**: Does training on successful encodings improve performance?
3. **Oracle-free**: Can AI encode from statute alone, with human validation?
4. **Multi-jurisdiction**: Does transfer learning work across countries?
5. **Real-time encoding**: Encode bills as they're drafted, before passage
