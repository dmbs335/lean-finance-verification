# Temporal Noninterference for Financial Backtesting

## Research question

A backtest should not let information that is causally unavailable at time t change a decision, fill, position, risk number, or P&L prefix at or before t.

Let D and D' be complete data histories. Define causal-prefix equivalence by:

```text
D ≡t D'
iff
every observation available by t has the same logical value in D and D'
```

A backtest engine B is temporally noninterfering when:

```text
D ≡t D'
→
prefix_t(B(D)) = prefix_t(B(D'))
```

The strategy, parameters, execution semantics, and exogenous randomness are held fixed. Only information outside the causal prefix may change.

This is the financial analogue of information-flow noninterference: future or unreleased data are high inputs, while past decisions and P&L are low outputs.

## Formal factorization theorem

`LeanFinance/Backtest/TemporalNoninterference.lean` separates the complete dataset, its causal prefix, the full engine run, a run reconstructed from only the prefix, and the output visible through the cutoff.

Lean proves that causal factorization implies temporal noninterference. The module also carries future-extension invariance, an epsilon-relaxed definition, a constructive counterexample type, a future-sensitive unsafe engine, and a separate observation-time versus availability-time contract.

## Executable semantic benchmark

`tools/temporal_noninterference/` is an exact finite metamorphic auditor. It checks temporal noninterference, strict availability, and source immutability across causal forward-fill, observation-only forward-fill, global-last fill, mutating global-last fill, and bidirectional interpolation semantics.

Registered mutations append future extreme rows, revise a future endpoint, reorder equivalent data, change timestamp representations, revise already-known past information, and change release availability. Only mutations preserving the causal prefix at every decision can count as noninterference violations.

For each violation the report includes changed decision count, exact rational mark distance, position distance, first divergence, and the smallest violating operation subset.

## Controlled result

Only `causalForwardFill` passes every contract. The unsafe engines separately demonstrate future-extension leakage, order sensitivity, release-time leakage, future-endpoint interpolation, and input mutation.

This controlled result does not claim that every external library with a similarly named method has the same behavior. It provides a contract and counterexample format for concrete adapters.

## GS Quant adapter direction

A direct adapter should freeze strategy serialization, engine configuration, pricing context, random seed, calendar, and fill/interpolation policy, then expose causal prefix, full run, output prefix, and source digests before and after execution.

The violation receipt should bind the gs-quant version, adapter version, engine configuration, base and mutated dataset digests, first divergent output, and minimized mutation witness.

## Assurance boundary

A green report is exact only for the supplied finite points, engines, decisions, and mutations. It does not prove external timestamp truth, adapter correctness, mutation-language completeness, absence of concurrency or floating-point effects, or future profitability.
