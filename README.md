# Lean Finance Verification

A Lean 4 research framework for **proof-carrying financial research**: market models,
constraint-driven dynamics, inverse-game abstractions, industrial bottlenecks,
evidence-separation theory, and machine-checkable backtest certificates.

## What this repository verifies

The project deliberately separates empirical estimation from formal claims. Python,
Rust, or another external system may estimate parameters and produce artifacts; Lean
checks the logical contract attached to those artifacts.

Current certificate properties include:

- every dataset used by a decision was available at the decision time;
- every derived feature has recursively closed lineage, with each input available by
  the feature's own generation time;
- the selected code/parameter trial appears in a commitment-chained search ledger;
- the complete ledger prefix is bound to a pre-decision anchor;
- RFC 3161 anchors are re-verified against verifier-selected TSA trust, including the
  original nonce, message imprint, signed response, certificate chain, and generation
  time;
- code, data, parameters, environment, features, and result are domain-separated by
  artifact kind, canonical schema, hash algorithm, and digest;
- an adapter handoff exposes a proof-carrying certificate rather than an opaque
  performance number.

The epistemic layer additionally proves and computes limits on verification itself:

- deterministic post-processing cannot amplify the distinctions present in evidence;
- a selected family of evidence channels verifies a claim exactly when it hits every
  claim-disagreement separator set;
- exploration completeness cannot be certified solely from a researcher's public
  declaration;
- an exact bounded synthesizer finds minimum-cost evidence and emits a counterexample
  for every cheaper candidate;
- a workflow CEGIS front end generates reachable attacks from transition semantics,
  discovers evidence-indistinguishable claim failures, instantiates new sensor
  channels, and rechecks the refined design in Lean.

These properties do **not** prove that a strategy is profitable, that raw data is true,
or that an empirical model is statistically correct. They prove the narrower
research-integrity and evidence-sufficiency claims encoded by the framework.

## Formal layers

```text
LeanFinance/
├── GameTheory/       heterogeneous players, beliefs, feasibility, best responses
├── Market/           order flow, linear price impact, Kyle-style quoting, liquidity
├── Constraints/      margin, VaR, redemption, and short-cover triggers
├── Dynamics/         market-state and equilibrium-regime transitions
├── Inference/        latent state, identification, and inverse-game boundaries
├── Epistemic/        verifiability, cut sets, finite synthesis, workflow semantics
├── StrategyEcology/  context-dependent causal strategy interactions
├── SupplyChain/      dynamic capacity, substitution, qualification, and rent claims
├── Backtest/         artifacts, PIT lineage, anchored search history, adapter contract
├── Certificate/      data, strategy, backtest, and verified-claim certificates
└── Generated/        adapter- and synthesizer-emitted concrete Lean witnesses
```

## Build

Lean is pinned in `lean-toolchain`.

```bash
lake build
```

GitHub Actions runs the empirical adapter, RFC 3161, exact evidence-synthesis, and
workflow CEGIS tests; checks generated artifacts byte-for-byte; and then runs the Lean
build.

## Evidence separation theory

`LeanFinance/Epistemic/` treats a complete research process as a hidden history, an
artifact bundle as an observation map, and an integrity statement as a proposition on
histories. The core criterion is that a verifiable claim must be constant on every
observational equivalence class.

The layer mechanizes verification non-amplification, epistemic cut-set duality,
constructive unverifiability witnesses, and a general no-self-certified-completeness
theorem. See [`docs/EVIDENCE_SEPARATION_THEORY.md`](docs/EVIDENCE_SEPARATION_THEORY.md)
for the semantic results.

## Exact evidence cut-set synthesis

The bounded synthesizer accepts complete candidate histories, evidence-channel
observations, and operational/privacy/trust costs. It constructs the separator
hypergraph, enumerates every channel subset, returns the minimum weighted-cost design,
and attaches an uncovered history pair to every lower-cost candidate.

```bash
python -m tools.evidence_synth synth \
  --model examples/evidence_synthesis/search_completeness.json \
  --out examples/evidence_synthesis/generated/synthesis.canonical.json \
  --lean-out LeanFinance/Generated/EvidenceSynthesis.lean \
  --pretty
```

`LeanFinance/Epistemic/FiniteSynthesis.lean` proves the executable checker sound and
turns generated lower-cost counterexamples into a Lean weighted-optimality theorem.
See [`docs/EVIDENCE_SYNTHESIS.md`](docs/EVIDENCE_SYNTHESIS.md) for the model, certificate,
Pareto frontier, and bounded-model interpretation.

## Counterexample-guided workflow synthesis

The workflow front end replaces hand-written adversarial worlds with a finite Boolean
transition system. It computes all terminal traces to a declared depth and runs an
exact master/oracle loop:

```text
minimum-cost repair satisfying known counterexamples
→ new indistinguishable claim-disagreement pair
→ separator constraint
→ repeat
```

```bash
python -m tools.workflow_cegis synth \
  --model examples/workflow_cegis/search_integrity.json \
  --report /tmp/lfv-workflow-cegis/report.canonical.json \
  --evidence-model /tmp/lfv-workflow-cegis/evidence-model.canonical.json \
  --synthesis /tmp/lfv-workflow-cegis/global-synthesis.canonical.json \
  --repair-synthesis /tmp/lfv-workflow-cegis/repair-synthesis.canonical.json \
  --workflow-lean LeanFinance/Generated/WorkflowSearch.lean \
  --evidence-lean LeanFinance/Generated/WorkflowEvidence.lean \
  --bridge-lean LeanFinance/Generated/WorkflowCEGIS.lean \
  --pretty
```

The checked-in workflow generates ten terminal histories automatically. The deployed
`selfReport + resultBundle + rfc3161Anchor` channels first fail on a future-data leak
and then on a hidden parameter sweep. CEGIS adds two narrow independent action receipts.
Exact repair synthesis proves those receipts cost less than a full executor log, while
global synthesis identifies the result bundle and timestamp as redundant for this
particular exploration-integrity claim.

The generated Lean modules prove trace-catalog completeness, bind claims and
observations back to workflow replay, materialize every refinement counterexample,
connect the rounds into one CEGIS chain, and exhaustively prove both greenfield and
mandatory-baseline repair optimality in the kernel. See
[`docs/COUNTEREXAMPLE_GUIDED_EVIDENCE_SYNTHESIS.md`](docs/COUNTEREXAMPLE_GUIDED_EVIDENCE_SYNTHESIS.md).

## Python reference adapter

The repository contains a dependency-free reference adapter that executes a declared
empirical command, canonicalizes its JSON result, hashes all research artifacts,
checks the committed search ledger and anchor, and emits both a canonical bundle and a
Lean `CertifiedAdapterOutput` witness.

The checked-in deterministic fixture uses a deliberately non-authoritative local
anchor:

```bash
python -m tools.lfv_adapter build \
  --spec examples/reference_adapter/experiment.json \
  --out /tmp/lfv-reference \
  --allow-local-anchor
```

A production ledger can instead be anchored by an RFC 3161 TSA:

```bash
python -m tools.lfv_adapter make-rfc3161-anchor \
  --ledger research/search-ledger.json \
  --tsa-url https://tsa.example.org/ \
  --rfc3161-ca-file trust/tsa-roots.pem \
  --out research/ledger-anchor.json
```

See [`docs/REFERENCE_ADAPTER.md`](docs/REFERENCE_ADAPTER.md) for the complete adapter
flow and [`docs/RFC3161_ANCHORS.md`](docs/RFC3161_ANCHORS.md) for timestamp trust and
archival assumptions.

## Research roadmap

1. Import real attack traces and perform transition-model refinement when a trace is
   absent from the current action semantics.
2. Learn reusable adversarial action schemas across backtests, dataset pipelines, and
   market-model workflows.
3. Add robust evidence portfolios against sensor compromise, correlated providers, and
   adaptive adversaries rather than assuming every selected channel is reliable.
4. Synthesize privacy-constrained and trust-diversified channels, including
   multi-provider anchor quorum and zero-knowledge execution receipts.
5. Run the complete workflow against a real point-in-time dataset and preserve the
   resulting attack catalog, evidence repair, and backtest certificate.

## Scope

This repository is research software. A Lean proof is only as strong as its formalized
history space, transition semantics, observation maps, assumptions, and the
cryptographic, data-lineage, execution, external-anchor, and trust-material evidence
supplied to the checker. Workflow exploration is complete only up to the declared depth
and action language. Exact synthesis is complete only over the generated bounded
histories and candidate channels. Neither establishes that every materially relevant
real-world attack has been modeled.
