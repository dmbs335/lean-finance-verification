# Executable Evidence-Obligation Taxonomy

`tools/evidence_taxonomy` converts the formal attack-coverage definitions into an exact finite classifier.

## Input

The tool consumes:

- one generated finite evidence model;
- designated honest histories;
- an ordered attack-history catalog.

For each attack it compares every designated honest history and computes the exact separator-channel hyperedges.

## Exact obligation semantics

A channel-selection mask covers an attack when it hits every honest–attack separator edge. The tool enumerates every channel mask, so an attack's obligation is represented by the complete set of covering selections rather than by a heuristic label.

Two attacks share an epistemic class exactly when their covering-mask sets are equal.

```text
same class
⇔
exactly the same channel portfolios cover both attacks
```

Subsumption is likewise exact:

```text
A subsumes B
⇔
every selection covering A also covers B
```

## Report

For every attack the canonical report records:

- honest–attack separator edges;
- number of covering selections;
- inclusion-minimal covering selections;
- minimum-cost selections;
- channels present in every covering selection;
- epistemic class and representative.

It additionally records:

- class membership;
- cross-class subsumption relations;
- cumulative Evidence Debt in the declared attack order;
- a domain-separated report digest.

## Controlled research-integrity corpus

The first corpus uses the 32-history model created after the observed cost-model-tampering refinement. It classifies:

```text
undeclaredBaseline
hiddenSweep
futureLeak
costModelTampering
dualAttack
```

The five traces form five distinct obligation classes.

### Atomic obligations

```text
undeclared baseline
  declaration boundary

hidden sweep
  execution boundary

future-data leak
  data-access boundary

cost-model tampering
  control-plane mutation boundary
```

The cost-model mutation has one required channel:

```text
targetedReceipt_tamperCostModel
```

The existing full execution log, selected result bundle, and RFC 3161 timestamp do not appear in its separator edge.

### Combination without novelty

`dualAttack` combines hidden sweep and future-data access. Its separator edge accepts either corresponding receipt. Therefore both atomic attacks evidence-subsume the combined attack.

In the declared corpus order, minimum cumulative debt evolves as:

```text
undeclared baseline       2
+ hidden sweep            4
+ future-data leak        6
+ cost-model tampering    8
+ dual attack             8
```

The combined implementation is a new trace but adds zero marginal Evidence Debt. This is the first executable distinction between implementation novelty and epistemic novelty.

## Usage

```bash
python -m tools.evidence_taxonomy build \
  --model examples/trace_refinement/generated/evidence-model.canonical.json \
  --config examples/evidence_taxonomy/research_integrity.json \
  --out /tmp/evidence-taxonomy.canonical.json \
  --pretty
```

The report can be independently recomputed with `verify`. Future attack-corpus work will use the class representative, subsumption graph, marginal debt, and connectivity loss to prioritize genuinely new research obligations.
