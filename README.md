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
- in the formal search-history model, the declaration and independent executor log
  form a mechanically proved minimal evidence cut set;
- an exact bounded synthesizer enumerates adversarial histories and channel subsets,
  finds minimum-cost evidence, and emits a counterexample for every cheaper candidate.

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
├── Epistemic/        verifiability, cut sets, impossibility, finite synthesis soundness
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

GitHub Actions runs the Python adapter and exact-synthesis tests, exercises a locally
generated RFC 3161 test PKI, checks generated artifacts byte-for-byte, and then runs the
Lean build.

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

The checked-in search-completeness model discovers `{selfReport, executorLog}` as the
unique inclusion-minimal set. A canonical result bundle and valid RFC 3161 timestamp do
not separate an honest run from an unreported parameter sweep, because both are
post-processings of the same visible declaration.

`LeanFinance/Epistemic/FiniteSynthesis.lean` proves the executable checker sound and
turns generated lower-cost counterexamples into a Lean weighted-optimality theorem.
See [`docs/EVIDENCE_SYNTHESIS.md`](docs/EVIDENCE_SYNTHESIS.md) for the model, certificate,
Pareto frontier, and bounded-model interpretation.

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

The TSA signing trust bundle is selected externally by the verifier and is hashed into
the evidence binding. See [`docs/REFERENCE_ADAPTER.md`](docs/REFERENCE_ADAPTER.md) for
the complete adapter flow and [`docs/RFC3161_ANCHORS.md`](docs/RFC3161_ANCHORS.md) for
signed timestamp issuance, verification, and trust assumptions.

## Research roadmap

1. Generate bounded adversarial histories from executable workflow transition systems
   instead of writing histories by hand.
2. Learn counterexample-guided model refinements when a new attack is absent from the
   current history space.
3. Synthesize privacy-constrained and trust-diversified evidence portfolios, including
   multi-provider anchor quorum.
4. Connect forced-flow composition, constraint activation, and regime-transition
   safety theorems end to end.
5. Run the reference adapter against a real point-in-time dataset and preserve the
   resulting certificate bundle as a reproducible research artifact.

## Scope

This repository is research software. A Lean proof is only as strong as its formalized
history space, observation maps, assumptions, and the cryptographic, data-lineage,
execution, external-anchor, and trust-material evidence supplied to the checker. RFC
3161 support verifies signed evidence but does not by itself prove TSA independence,
revocation status, or long-term archival validity. Exact synthesis is complete over the
declared bounded model and candidate channel language; it does not prove that the model
contains every real-world adversarial history.
