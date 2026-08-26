# Unified Research Version Space

## One admissible-world calculus

Represent one complete research world as:

```text
v = (D, M, S, X, U)
```

where:

- D is the data vintage and availability history;
- M is the pricing, factor, or risk-model version;
- S is the disclosed or hidden adaptive search history;
- X is the execution, cost, fill, and capacity semantics;
- U is the security universe and identifier-resolution state.

For evidence E and cutoff t, the version space is:

```text
V_t(E) = { v | v is admissible under E at t }
```

This subsumes several earlier modules. PIT leakage varies D, model revision varies M, search debt varies S, execution realizability varies X, and survivorship or identifier drift varies U.

## Certifiable metric range

For any integer-valued metric f, define:

```text
C_f(E,t) = [ inf_{v in V_t(E)} f(v),
             sup_{v in V_t(E)} f(v) ]
```

The Lean formalization avoids assuming that extrema exist in every abstract space. An `ExactMetricRange` carries proofs that its lower endpoint is the greatest valid lower bound and its upper endpoint is the least valid upper bound.

If stronger evidence refines weaker evidence:

```text
V_t(E_strong) subseteq V_t(E_weak)
```

then Lean proves:

```text
lower(E_weak) <= lower(E_strong)
upper(E_strong) <= upper(E_weak)
```

Thus exact ranges are nested under evidence refinement. When at least one world survives and every surviving world has the same metric, the exact range collapses to a point.

## Interactions matter

An additive bias decomposition can hide interactions. Revised data may be especially valuable to an adaptive search, and optimistic execution assumptions may compound a survivor-universe bias.

The controlled executable model therefore includes explicit interaction terms. It enumerates all 32 binary worlds, computes the exact metric range under every evidence subset, and reports dimension-flip effects across all contexts.

## Shapley revision attribution

To allocate the total baseline-to-all-alternative change without depending on an arbitrary replacement order, the analyzer computes exact Shapley values:

```text
phi_i = sum_{S subset N without i}
        |S|! (n-|S|-1)! / n!
        * [ f(S union {i}) - f(S) ]
```

For the controlled fixture the 130-point difference is allocated as:

```text
data       52.5
model      10
search     42.5
execution  17.5
universe    7.5
```

The data-search interaction of 25 is split equally between data and search; the execution-universe interaction of 5 is split equally between execution and universe.

## Minimum evidence for a target interval

The evidence-design problem is:

```text
minimize Cost(E')
subject to Width(C_f(E',t)) <= epsilon
```

The exact solver enumerates every channel subset. In the controlled fixture no evidence leaves range [20,150]. `pitDataReceipt + searchLedger` costs 4 and narrows it to [20,55], satisfying epsilon=40. Every cheaper candidate carries its minimum/maximum admissible worlds as a constructive width counterexample.

## Relationship to other project modules

```text
Temporal Noninterference
  protects output prefixes against changes outside D's causal prefix

Certifiable Alpha / Risk
  chooses f(v) as alpha, VaR, ES, hedge error, or deployable PnL

Evidence Debt
  is the minimum evidence cost needed to obtain a target claim or interval

Certificate Composition
  binds the evidence and outputs to the same D-M-S-X-U pipeline

Scenario Basis Synthesis
  can treat adversarial market states as another world coordinate
```

## Assurance boundary

The formal theorems are relative to the declared admissibility relation and exact-range certificates. The Python result is exact only for the binary dimensions, interactions, and channel language in the fixture.

The module does not establish the empirical size of any effect, completeness of the five coordinates, truth of external timestamps, correctness of a concrete library adapter, or future profitability.
