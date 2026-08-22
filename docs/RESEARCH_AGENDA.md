# Research Agenda

## North Star

> Determine the minimum evidence structure that makes an empirical claim verifiable under incomplete workflow semantics, expanding adversarial models, correlated provider failures, privacy constraints, and bounded computational resources.

The repository is no longer primarily a collection of financial toy models. Its central contribution is a theory and executable system for reasoning about what empirical evidence can and cannot establish.

## Completed foundation

### Integrity layer

- point-in-time dataset and recursive feature-lineage contracts;
- domain-separated artifact identities and canonical bundles;
- committed search ledgers and signed RFC 3161 anchors;
- executable empirical adapter and generated Lean witnesses.

### Evidence-separation layer

- verification non-amplification;
- separator cut-set duality;
- no self-certified completeness;
- constructive unverifiability witnesses;
- exact minimum-cost evidence synthesis.

### Workflow layer

- bounded finite workflow semantics;
- automatic adversarial-history enumeration;
- counterexample-guided evidence repair;
- observed-trace-driven action/state refinement;
- conservative old-semantics preservation;
- finite CEGIS convergence and global optimality.

### New structural layer

- Evidence Debt monotonicity and attack-pressure/sensor-relief balance;
- channel and trust-domain Epistemic Connectivity;
- evidence-obligation equivalence and subsumption;
- downstream Observation Boundary impossibility;
- transition-level safety–observability duality;
- exact robust synthesis under domain failures;
- executable attack taxonomy and marginal-debt analysis.

## Priority A — Semantics uncertainty

### A1. Action-schema version spaces

One trace normally supports multiple guard and effect hypotheses. Preserve the full finite version space instead of selecting one convenient refinement.

Deliverables:

```text
ConsistentWithTrace(schema, trace)
finite guard/effect hypothesis language
positive and negative trace constraints
model-family history generation
```

### A2. Robust synthesis over model families

Counterexamples become pairs of model/history worlds:

```text
(model₁, history₁)
(model₂, history₂)
```

A selected portfolio must verify the claim in every model consistent with the observed traces.

### A3. Active instrumentation

When the version space contains semantically different models, synthesize the next observation or controlled experiment that maximally splits the remaining model family per unit cost.

## Priority B — Fault resilience

### B1. Robust portfolio synthesis beyond one-domain loss

Extend the exact solver to:

- arbitrary connectivity levels;
- correlated fault hypergraphs;
- provider capabilities and shared dependencies;
- cost–connectivity Pareto frontiers.

### B2. Concrete independent providers

Instantiate the theory with:

- multiple RFC 3161 providers;
- transparency-log inclusion and consistency proofs;
- independent execution receipts;
- separate declaration registries;
- CI and cloud administrative domains.

### B3. Adaptive adversaries

Allow the attacker to observe deployed channels before choosing a workflow deviation. Compare static, randomized, and dynamically refreshed evidence portfolios.

## Priority C — Attack-corpus science

### C1. Expand the corpus

Add controlled traces for:

```text
failed-run deletion
seed cherry-picking
benchmark switching
metric switching
evaluation-window movement
universe survivorship filtering
future constituent use
restatement substitution
corporate-action alteration
environment substitution
adapter replacement
provider substitution
off-pipeline execution
```

### C2. Discover evidence boundaries

Determine whether dozens of concrete attacks collapse into a small basis such as:

```text
declaration
execution
data access
configuration mutation
evaluation
publication
environment
external time
```

### C3. Novelty ranking

Rank new traces by:

- obligation-equivalence novelty;
- marginal Evidence Debt;
- connectivity loss;
- new trust-domain requirement;
- unique-separator status.

## Priority D — Actual financial study

### D1. Data-vintage certificate

Represent first publication, revision time, vendor retrieval, supersession, and exact content identity.

### D2. Point-in-time universe certificate

Include listing, delisting, index membership, eligibility rules, and exclusion lineage.

### D3. Corporate-action transform certificate

Derive adjusted series from raw prices and event streams instead of trusting opaque adjusted prices.

### D4. First proof-carrying study

Run a simple monthly momentum or ranking strategy end to end. The target is not novel alpha; it is a complete research-integrity artifact with controlled attack injections and evidence-cost analysis.

## Priority E — Scalability

### E1. Finite domains beyond Boolean state

Add executable bounded enums, counters, timestamps, artifact identities, trial status, and trust-domain identifiers.

### E2. Symbolic backend

Use BDD, SAT/SMT, MaxSAT, or ILP outside the trusted boundary to propose candidates and counterexamples. Retain Lean checking of every certificate.

### E3. Compositional verification

Prove when local certificates for ingestion, feature generation, search, evaluation, publication, and anchoring compose into a global claim—and construct cross-boundary counterexamples when they do not.

## Deferred

The following are intentionally postponed until their governing theory is mature:

- product UI and broad CLI polishing;
- zero-knowledge receipts before separator predicates are stable;
- arbitrary market-state theorem expansion unrelated to evidence sufficiency;
- unbounded numeric dynamics;
- large-scale packaging and release automation.

## Next sequence

```text
1. action-semantics version space
2. model-family robust synthesis
3. active instrumentation
4. expanded attack corpus
5. real point-in-time backtest
```

This sequence targets the remaining central weakness: exact synthesis is currently robust over histories, channels, and faults, but still conditions on one selected workflow semantics.
