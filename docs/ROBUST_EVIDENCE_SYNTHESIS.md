# Robust Evidence Synthesis

Ordinary evidence synthesis asks for the cheapest selected channel family that separates every claim-disagreement history pair. Robust synthesis asks a stronger question:

> What is the cheapest portfolio that remains verifying after every allowed evidence-provider failure?

## Finite trust-domain model

Each channel declares:

```text
observation semantics
operational/privacy/trust cost
trust domain
```

A trust domain represents correlated control. Multiple artifacts, mirrors, or signatures in one domain disappear together when that domain is compromised.

The model also declares a required connectivity level `r`. The exact solver enumerates every duplicate-free failed-domain set of size smaller than `r`.

```text
r = 1
  ordinary verification

r = 2
  survive any one trust-domain failure

r = 3
  survive any two trust-domain failures
```

## Exact solver

For every selected channel subset and every allowed domain fault, the solver removes channels in failed domains and checks every claim-disagreement separator edge.

It emits:

- separator channels and distinct separator domains for each history pair;
- every allowed finite fault scenario;
- the minimum weighted-cost robust portfolio;
- every equal-cost optimum;
- inclusion-minimal robust portfolios;
- a concrete failed-domain and uncovered-edge witness for every cheaper candidate;
- an impossibility witness when one edge has fewer separator domains than the requested connectivity.

## Lean checker

`FiniteRobustSynthesis.lean` defines:

```lean
liveSelection
BoundedRobustSelectionVerifies
boundedRobustVerifiesBool
```

and proves Boolean soundness and completeness. It also proves that a bounded result lifts to the abstract `RobustlyVerifies` semantics when the history and fault lists are complete.

The generated finite candidate type is checked exhaustively in Lean:

```text
all channel masks
×
all enumerated trust-domain faults
×
all bounded history disagreements
```

The resulting `BoundedRobustSynthesisCertificate` proves both robust verification and minimum cost.

## Connectivity-two search example

The example contains two independent obligations:

```text
honest ↔ hidden sweep
  execution evidence

honest ↔ undeclared baseline
  declaration evidence
```

Candidate channels include:

```text
selfReport                 domain researcher
declarationRegistry        domain registry
executorA                  domain executorA
executorMirror             domain executorA
executorB                  domain executorB
resultBundle               domain researcher
rfc3161Anchor              domain tsa
```

`executorMirror` is cheap but shares the `executorA` domain. It does not add independent connectivity.

The minimum connectivity-two portfolio is:

```text
selfReport
declarationRegistry
executorMirror
executorB
```

with weighted cost 10.

The declaration edge retains `researcher` and `registry`; the hidden-sweep edge retains `executorA` and `executorB`. Removing any one domain still leaves one selected separator for each edge.

Changing `executorB` to the `executorA` domain makes the requested verification impossible, regardless of how many same-domain executor artifacts are selected.

## Design consequence

The relevant redundancy unit is not artifact count:

```text
number of selected artifacts
```

but separator-domain connectivity:

```text
minimum number of independent selected separator domains
across all claim-disagreement pairs
```

This is the formal basis for later multi-anchor, multi-executor, and provider-diversification policies.
