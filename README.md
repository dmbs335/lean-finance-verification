# Lean Finance Verification

A Lean 4 and Python framework for **proof-carrying financial research**. The repository does not try to prove that an investment strategy will be profitable. It asks a narrower and more fundamental question:

> Given hidden research histories, model ambiguity, fallible evidence providers, and market-capacity constraints, what can a reported investment result actually justify?

The system models complete research workflows, generates adversarial histories, identifies evidence-indistinguishable claim failures, synthesizes minimum-cost evidence repairs, checks point-in-time data and search provenance, and carries the resulting bounded claims into certifiable-alpha, portfolio, crowding, liquidation, event-study, and research-agent layers.

## Core idea

A research claim is verifiable only when it is constant on every hidden history that produces the same selected evidence.

```text
hidden research histories
        ↓ observation maps
 evidence-equivalence classes
        ↓
claim constant in each class?
   yes → verifiable
    no → constructive counterexample
```

Hashes, signatures, timestamps, reports, and Lean proofs preserve distinctions already present in evidence. They cannot recover an upstream event that never crossed the observation boundary.

## Integrated research path

```text
Evidence Separation Theory
        ↓
Exact / CEGIS Evidence Synthesis
        ↓
Trace-Driven Model Refinement
        ↓
PIT Data and Search Provenance
        ↓
Certifiable Alpha and Residual Uncertainty
        ↓
Evidence-Adjusted Portfolio Selection
        ↓
Certifiability–Crowding and Capacity Death
        ↓
Epistemic Crowding and Liquidation
        ↓
Preregistered Matched Event Study
        ↓
Fail-Closed Research Agent and Human Review
```

## What is implemented

### Evidence-separation theory

`LeanFinance/Epistemic/` formalizes:

- observational equivalence and claim verifiability;
- verification non-amplification;
- evidence cut-set duality;
- no self-certified exploration completeness;
- observation-boundary impossibility;
- evidence-debt monotonicity;
- first-violation transition separation;
- channel and trust-domain connectivity;
- multi-claim composition;
- conservative workflow refinement;
- finite CEGIS convergence;
- action-semantics version spaces and robust model-family synthesis.

The executable tools include exact subset synthesis, workflow CEGIS, attack-trace refinement, evidence-obligation taxonomy, robust provider portfolios, multi-claim optimization, and symbolic branch-and-bound search.

### Proof-carrying backtests

`LeanFinance/Backtest/`, `LeanFinance/Certificate/`, and `tools/lfv_adapter/` cover:

- canonical, domain-separated artifact identities;
- recursively closed point-in-time feature lineage;
- dated universe and corporate-action contracts;
- commitment-chained search ledgers;
- preregistered code, parameters, metrics, benchmarks, and cost models;
- RFC 3161 timestamps with verifier-selected trust;
- signed transparency receipts and trust-domain quorum;
- signed point-in-time vendor package import;
- selective-disclosure and experimental zero-count execution receipts;
- generated Lean witnesses and byte-for-byte reproducibility checks.

### Certifiable alpha

`LeanFinance/Alpha/` and the corresponding tools distinguish:

```text
observed alpha
= economic alpha
+ research-process attack bias
+ risk-model bias
+ sampling noise
```

The controlled fake-alpha benchmark can exactly recover a **synthetic distortion-free ground truth** because the injected attacks are known. The separate economic decomposition proves that attack-bias removal still leaves model and sampling error. `tools/certifiable_alpha_interval/` then combines:

- model-envelope uncertainty;
- unresolved upward attack inflation;
- deployment-cost uncertainty;

into a defensible finite interval rather than one overconfident point estimate.

### Evidence-adjusted portfolios

`LeanFinance/Portfolio/` and `tools/evidence_portfolio/` compare conventional and evidence-aware finite selection using:

```text
certifiable lower alpha
- conventional risk penalty
- evidence debt
+ robustness reward
- shared dependency concentration penalty
```

The objective weights are declared governance inputs, not claimed market prices. The solver exactly enumerates the finite candidate space and emits complete score decompositions.

### Certifiability–crowding and alpha-death modes

`LeanFinance/Alpha/CertifiabilityCrowding.lean` and `tools/certifiability_crowding/` formalize the conditional mechanism:

```text
stronger evidence
→ higher allocator confidence
→ more capital
→ greater impact / capacity use
→ lower deployable alpha
```

The model separates:

- **epistemic death** — the evidence-supported lower bound is nonpositive;
- **capacity death** — gross economic alpha is positive but impact consumes the deployable edge;
- **ecological decay** — the gross edge itself falls after market adaptation.

A zero-impact control shows that evidence alone does not destroy alpha; the mechanism requires an allocation-and-capacity channel.

### Epistemic crowding and liquidation

`LeanFinance/Market/EpistemicLiquidation.lean` and `tools/epistemic_liquidation/` distinguish return correlation from shared data, model, execution, and evidence-provider dependencies.

The report separates:

- **latent hidden epistemic crowding** — low return correlation plus shared research-validity dependencies;
- **realized hidden common risk** — a shared dependency actually fails and synchronizes first-round withdrawals.

A two-round controlled simulator connects evidence withdrawal to market impact and margin/funding feedback. These are transparent research equations, not calibrated claims about current markets.

### Preregistered event studies

`LeanFinance/Market/EpistemicEventStudy.lean` and `tools/epistemic_event_study/` turn the liquidation hypothesis into a fail-closed matched event-study protocol. The plan fixes before analysis:

- event and registration timestamps;
- failed-domain exposure;
- return, factor, holdings, and liquidity matching tolerances;
- pretrend tolerance;
- minimum event-window difference-in-differences.

A bounded certificate is emitted only when every registered gate passes. The checked-in data are synthetic and do not establish real-market causality.

### Proof-carrying research agent

`LeanFinance/ResearchAgent/` and `tools/research_agent/` provide two related contracts.

The registered-plan harness runs seven deterministic analyses in order and binds their reports plus the cross-certificate composition result by canonical digest:

```text
fake-alpha audit
→ alpha interval
→ evidence-adjusted portfolio
→ crowding stress
→ liquidation stress
→ event study
→ certificate composition
→ bounded certificate
```

The candidate gate has only three machine outcomes:

```text
advanceToHumanReview
repairEvidence
rejectCandidate
```

It exactly synthesizes minimum-cost evidence repairs, rejects unrepresentable gaps, and rejects process-valid candidates whose impact- and capacity-adjusted lower bound is nonpositive. Autonomous deployment is intentionally absent.

## Repository layout

```text
LeanFinance/
├── Alpha/             certifiable alpha, uncertainty, fake-alpha, crowding
├── Backtest/          artifacts, PIT lineage, ledgers, adapter contracts
├── Certificate/       normalized data, strategy, and result certificates
├── Epistemic/         verifiability, cut sets, CEGIS, debt, robustness
├── Market/            microstructure plus epistemic liquidation/event study
├── Portfolio/         evidence-adjusted finite allocation theory
├── ResearchAgent/     ordered proof gates and candidate decisions
├── GameTheory/        players, beliefs, feasibility, responses
├── Constraints/       leverage, margin, VaR, redemption, forced flows
├── Dynamics/          states, regimes, and transitions
├── Inference/         latent-state and identification boundaries
├── StrategyEcology/   context-dependent strategy interactions
├── SupplyChain/       capacity, qualification, substitution, rents
└── Generated/         machine-emitted Lean witnesses

tools/
├── lfv_adapter/                 proof-carrying backtest adapter and timestamps
├── evidence_synth/              exact separator / hitting-set synthesis
├── workflow_cegis/              workflow exploration and evidence repair
├── trace_refinement/            observed attack-trace model refinement
├── evidence_taxonomy/           separator-signature attack taxonomy
├── robust_evidence/             provider / trust-domain resilient portfolios
├── model_family_synth/          trace-consistent semantics version spaces
├── multiclaim_synth/            shared evidence across multiple claims
├── symbolic_evidence/           branch-and-bound finite synthesis
├── fake_alpha_benchmark/        controlled distortion recovery
├── certifiable_alpha_interval/  residual alpha uncertainty synthesis
├── evidence_portfolio/          exact evidence-adjusted allocation
├── certifiability_crowding/     confidence, allocation, capacity lifecycle
├── epistemic_liquidation/       dependency shocks and funding contagion
├── epistemic_event_study/       preregistered matched event analysis
├── certificate_composition/     cross-certificate binding synthesis
├── research_agent/              ordered research and candidate review gates
├── pit_study/                   point-in-time study contracts
├── pit_vendor_import/           signed vendor package verification
├── external_quorum/             signed external evidence quorum
├── selective_receipt/           selective execution disclosure
└── zk_receipt/                  experimental zero-count proof backend
```

## Build and validation

Lean is pinned in `lean-toolchain`.

```bash
lake build
```

Run an individual Python suite:

```bash
python -m unittest discover -s tools/research_agent/tests -v
```

The main GitHub Actions workflow runs every Python suite, canonical/generated artifact reproduction, cryptographic fixtures, and the complete Lean build.

## Representative commands

### Exact evidence synthesis

```bash
python -m tools.evidence_synth synth \
  --model examples/evidence_synthesis/search_completeness.json \
  --out /tmp/evidence.json \
  --lean-out /tmp/EvidenceSynthesis.lean
```

### Workflow CEGIS

```bash
python -m tools.workflow_cegis synth \
  --model examples/workflow_cegis/search_integrity.json \
  --report /tmp/workflow-report.json \
  --evidence-model /tmp/evidence-model.json \
  --synthesis /tmp/global-synthesis.json \
  --repair-synthesis /tmp/repair-synthesis.json \
  --workflow-lean /tmp/WorkflowSearch.lean \
  --evidence-lean /tmp/WorkflowEvidence.lean \
  --bridge-lean /tmp/WorkflowCEGIS.lean
```

### Registered research plan

```bash
python -m tools.research_agent --repository-root . run \
  --plan examples/research_agent/plan.json \
  --out /tmp/research-agent.json
```

### Candidate review and evidence repair

```bash
python -m tools.research_agent gate-candidates \
  --batch examples/research_agent/candidates.json \
  --out /tmp/research-candidates.json
```

### Learning app

```bash
python -m http.server 8000
```

Open `http://localhost:8000/learning-app/`. The curriculum is linked directly to repository sources and checked for drift in CI.

## Assurance boundary

A successful build can establish:

- logical consequences of declared Lean definitions and premises;
- exact results over explicitly finite histories, models, channels, portfolios, and failure scenarios;
- successful verification of external signatures, hashes, timestamp responses, manifests, Merkle paths, and schemas by the supplied Python/OpenSSL code.

It does **not** establish:

- future profitability or investment suitability;
- truth or lawful provenance of external data merely because it is signed;
- completeness of the real-world attack or model family;
- actual independence of nominally different providers;
- statistical correctness of an expected-alpha estimate;
- calibrated allocator response, market impact, capacity, or causal market effects;
- production security of the experimental private-proof backend;
- correctness of Python, OpenSSL, cryptographic primitives, or the host system.

See [`docs/FORMAL_CLAIMS.md`](docs/FORMAL_CLAIMS.md) for the assurance classification.

## Research status and next milestone

The theory and controlled executable layers are mature enough that the highest-value next work is empirical rather than another parallel synthetic implementation:

1. a lawful strict point-in-time study using authenticated original vintages;
2. a dated methodology/vendor-shock dataset with strategy dependency, flow, holdings, factor, and liquidity controls;
3. statistical calibration of certifiable-alpha intervals;
4. compositional verification across full data → feature → search → evaluation → publication pipelines;
5. independent provider deployments and cryptographic review.

This repository remains research software. Every strong claim is relative to its history language, model family, observation map, failure policy, data evidence, and operational trust boundary.
