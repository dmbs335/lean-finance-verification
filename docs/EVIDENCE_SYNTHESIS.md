# Exact Evidence Cut-Set Synthesis

`tools/evidence_synth` turns the semantic cut-set duality in
`LeanFinance/Epistemic/CutSet.lean` into an executable bounded synthesizer.

The input is a finite adversarial model:

```text
histories
  complete candidate worlds considered by this bounded analysis

claim(history)
  the truth value to be verified

channel(channel, history)
  what each evidence source would reveal in each world

cost(channel)
  operational, privacy, and external-trust burden
```

For every pair of histories on which the claim disagrees, the synthesizer computes the
channels that distinguish the pair. Those channel sets are the hyperedges of the
evidence-separation problem.

A selected channel set verifies the bounded claim exactly when it intersects every
hyperedge.

## Exact solver

The solver enumerates every subset of up to 12 channels. It computes:

- all claim-disagreement history pairs;
- the exact separator set for each pair;
- whether verification is impossible because one separator set is empty;
- every verifying channel set;
- inclusion-minimal verifying sets;
- the Pareto frontier over operational, privacy, and trust costs;
- a minimum weighted-cost selection;
- for every cheaper selection, a concrete uncovered history pair.

The maximum channel count is deliberately small. This is an exact bounded research
tool, not a claim that arbitrary evidence-design instances can be solved without the
usual combinatorial cost.

## Search-completeness example

The checked-in model considers three complete histories:

```text
honest
  baseline declared, baseline executed

hiddenSweep
  baseline declared, baseline and hidden sweep executed

undeclaredBaseline
  nothing declared, baseline executed
```

It exposes four possible channels:

```text
selfReport
executorLog
resultBundle
rfc3161Anchor
```

The exact separator hypergraph is:

```text
honest ↔ hiddenSweep
  {executorLog}

honest ↔ undeclaredBaseline
  {selfReport}
```

The canonical result therefore selects:

```text
{selfReport, executorLog}
```

The result bundle and valid RFC 3161 timestamp do not appear in either separator set.
They may authenticate the researcher's visible declaration, but they do not reveal an
execution event that was omitted from that declaration.

Run the synthesis with:

```bash
python -m tools.evidence_synth synth \
  --model examples/evidence_synthesis/search_completeness.json \
  --out examples/evidence_synthesis/generated/synthesis.canonical.json \
  --lean-out LeanFinance/Generated/EvidenceSynthesis.lean \
  --pretty
```

Reproducibility is checked with:

```bash
python -m tools.evidence_synth check-generated \
  --model examples/evidence_synthesis/search_completeness.json \
  --certificate examples/evidence_synthesis/generated/synthesis.canonical.json \
  --lean LeanFinance/Generated/EvidenceSynthesis.lean
```

## Proof-carrying output

`LeanFinance/Epistemic/FiniteSynthesis.lean` defines:

- an executable bounded verification checker;
- a soundness theorem connecting checker acceptance to semantic channel verification;
- `BoundedCounterexample`, a concrete missed separator edge;
- `BoundedSynthesisCertificate`, containing a selected verifying set and a
  counterexample for every lower-cost candidate.

The generated Lean module enumerates the complete bounded candidate language. For the
selected set it proves bounded verification by computation. For each lower-cost
candidate it materializes a history pair that the candidate fails to distinguish.
The generic theorem then derives weighted-cost optimality:

```lean
selectedCostLeOfCandidateVerifies
```

This is stronger than trusting the Python optimizer's numeric answer. The optimizer
must provide the semantic lower-bound witnesses needed by Lean.

## Canonical certificate

The JSON certificate records:

- a domain-separated SHA-256 digest of the normalized model;
- all separator hyperedges;
- candidate and verifying-set counts;
- the selected cost vector and weighted cost;
- all equal-cost optima;
- inclusion-minimal sets;
- the multi-objective Pareto frontier;
- every lower-cost failure and its uncovered edge;
- a digest over the complete synthesis certificate.

`verify` recomputes the exact problem from the model and rejects any discrepancy:

```bash
python -m tools.evidence_synth verify \
  --model examples/evidence_synthesis/search_completeness.json \
  --certificate examples/evidence_synthesis/generated/synthesis.canonical.json
```

## Interpretation boundary

The synthesis result is exact relative to the bounded model. It does not prove that the
history generator contains every real adversarial behavior or that a channel's modeled
observation accurately describes a deployed system.

There are therefore two separate completeness questions:

1. **solver completeness** — every subset of the declared channel list is enumerated;
2. **model completeness** — every materially relevant real-world history and channel
   behavior is represented.

The first is handled by the exact enumerator and generated candidate language. The
second remains a scientific modeling obligation. The next research step is to generate
bounded adversarial histories automatically from workflow transition systems and to
refine a model whenever an omitted attack produces a new indistinguishability witness.
