# Temporal Noninterference for Financial Backtests

A backtest is temporally noninterfering when changing information unavailable by a decision cutoff cannot change the output at that cutoff.

For hidden histories `D` and `D'`:

```text
D ≡t D'
```

means every input whose `availableAt` is no later than `t` has the same value in both histories. A fixed computation `B` is safe when:

```text
D ≡t D'  ⇒  B(D, t) = B(D', t)
```

The Lean definition treats the strategy, engine version, calendar, pricing model, execution model, and random seed as fixed inside `B`. Only the hidden input history varies.

## Temporal Composition Law

A real backtest is a pipeline:

```text
raw data → imputation → feature → signal → order → fill → PnL
```

The formal layer proves a compositional result: when a feature transform preserves every available input prefix and the downstream consumer reads only the derived prefix available by its decision time, their composition is temporally noninterfering.

This is stronger than checking that one final dataset has no obviously future-dated rows. Every transformation boundary must preserve the causal prefix.

## Exact metamorphic oracle

`tools/temporal_noninterference/` runs two independent comparisons:

1. **future-extension invariance** — append observations unavailable by the cutoff and compare every output through the cutoff;
2. **availability projection** — compare a computation over the complete container with the same computation over only observations available by each query.

The tool also treats source mutation as a separate safety failure. A data source that inserts missing rows into the caller's object can poison later feature calculations even when one returned value happens to be numerically correct.

Each output contains an exact rational value, threshold position, mutation trace, and first-divergence witness. A certificate is emitted only when both temporal checks pass and the source remains immutable.

## gs-quant controlled regression

The checked-in fixture mirrors the public reproduction in `goldmansachs/gs-quant#375`:

```text
2024-01-02 … 2024-01-05 values 100 … 103
missing query 2024-01-06
future extension through 2024-01-15 ending at 999
```

A causal forward fill returns 103 in both worlds. The modeled append-tail forward fill returns 103 for the prefix-only history but 999 after the future extension, reversing a threshold position. It also inserts a missing query marker, representing the reported caller-series mutation.

Two-sided interpolation fails for a different reason: its right endpoint may not yet be available at the query time.

The fixture is a dependency-free semantic model of the public behavior, not an assertion that every gs-quant version or index representation has the same defect.

## First-divergence witness

For unsafe pipelines the report records:

```text
kind: future_extension or availability_projection
time: first affected decision time
left/right exact values
left/right positions
```

This witness is suitable for trace refinement:

```text
counterexample
→ identify first noncausal transform
→ extend action/data semantics
→ synthesize a missing causal receipt or repair
→ add the minimized trace to regression corpus
```

## Assurance boundary

The Lean theorem proves the stated relation for declared histories and functions. The Python benchmark is exact only for its finite operations, observations, and query times. It does not establish the causality of an arbitrary third-party engine until an adapter captures that engine's actual input and output traces under the same metamorphic transformations.
