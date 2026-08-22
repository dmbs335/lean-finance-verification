# Formal Claims and Trust Boundaries

This document separates four categories that should not be conflated:

```text
proved in Lean
checked by exhaustive bounded computation
validated by an external cryptographic/runtime component
assumed or not yet modeled
```

## 1. General theorems proved in Lean

### Evidence separation

- A claim is verifiable exactly when its truth value is constant on every evidence-equivalence class.
- Proposition-valued verifiability is equivalent to the repository's identification notion.
- Deterministic post-processing cannot amplify verification power.
- A constructive indistinguishable history pair refutes verification.

### Cut-set duality

- A selected channel family verifies a claim iff it hits the separator set of every claim-disagreement history pair.
- Adding channels cannot destroy verification.
- A unique separator is necessary in every verifying selection.

### Completeness impossibility

- Researcher-generated declaration evidence alone cannot certify that no hidden trial occurred.
- Hashes, canonical serialization, signatures, or generated proof terms over the same self-certified record cannot repair the missing observation.

### Conservative workflow refinement

- Embedded old traces replay to embedded old states in a conservative refined workflow.
- Old terminal classifications are preserved.
- Claim and observation preservation can be carried as independent refinement contracts.

### Evidence Debt

- Conservatively adding adversarial histories cannot reduce minimum verification cost for a fixed candidate language.
- Expanding the candidate sensor language cannot increase minimum verification cost.
- Attack pressure and sensor relief satisfy the proved debt-balance identity.

### Epistemic Connectivity

- Robust verification under an arbitrary allowed-fault model is equivalent to retaining a live selected separator for every claim-disagreement pair under every allowed fault.
- Higher connectivity implies every lower connectivity level.
- Trust-domain connectivity counts correlated provider failures rather than raw artifact count.

### Evidence-obligation taxonomy

- Obligation equivalence is mutual subsumption and forms an equivalence relation.
- Equal pointwise separator signatures imply equal obligations.
- A constructive covering-selection counterexample proves two attacks are obligation-inequivalent.

### Observation boundaries

- Evidence factorization through a boundary is transitive.
- Downstream deterministic evidence cannot verify a claim that is already unverifiable at the boundary.
- The theorem applies to selected channel families and arbitrary downstream post-processing.

### Transition separation

- Persistent and specific detectors covering every declared violation-transition class suffice to verify the terminal claim.
- Under a complete transition witness basis, verification is equivalent to transition coverage.
- A silent claim-changing violation pair refutes verification.

### CEGIS convergence

- A strictly decreasing natural progress measure bounds the number of counterexample rounds.
- A complete verified oracle establishes global feasibility.
- An exact final master over discovered constraints is globally minimum cost against every fully feasible candidate.

## 2. Bounded results checked exhaustively

The following claims are exact only over their explicitly generated finite histories, channels, candidates, faults, and depth bounds.

### Search-integrity workflow

- Ten terminal histories are generated up to the declared workflow depth.
- The initial declaration/result/timestamp portfolio misses future-data and hidden-sweep histories.
- Two targeted receipts form the minimum incremental repair.

### Observed cost-model tampering refinement

- The original action alphabet cannot resolve `tamperCostModel`.
- The refined Boolean workflow replays the observed trace to a terminal claim violation.
- The refined model enumerates 32 terminal histories and seven channels.
- `targetedReceipt_tamperCostModel` is the unique separator for the named honest/attack pair.
- Mandatory-baseline and greenfield Evidence Debt each increase by two units.

### Robust synthesis example

- Every channel subset and every zero-or-one trust-domain failure is checked.
- The minimum connectivity-two portfolio costs ten.
- Same-domain executor mirroring does not replace an independent executor domain.

### Attack taxonomy example

- Five selected research-integrity traces form five distinct obligation classes in the declared finite model.
- Hidden-sweep and future-data atomic obligations each subsume the dual attack.
- The dual attack adds zero marginal debt after both atomic obligations are already covered.

## 3. Externally validated properties

### Reference adapter

Python recomputes canonical encodings, artifact digests, ledger commitments, lineage ordering, and generated bundle material. Lean verifies the resulting logical relationships.

### RFC 3161

OpenSSL validates the original request/response pair, message imprint, nonce, CMS signature, certificate chain, timestamp-signing purpose, and generation time against verifier-selected trust material.

These checks are outside the Lean kernel. Their exact binary, operating-system, certificate-distribution, and runtime integrity remain external assumptions.

## 4. Assumptions and currently unproved claims

The repository does not currently prove:

- that raw market or accounting data is true;
- that the workflow action language contains every real attack;
- that one observed trace identifies globally correct action semantics;
- that selected evidence providers are honest or independent unless a fault model states so;
- that cryptographic primitives remain collision-resistant indefinitely;
- certificate revocation or long-term archival validity;
- profitability, statistical significance, or future performance of a strategy;
- causal validity of an empirical market model merely because its artifact lineage is certified;
- completeness beyond declared finite depths and candidate languages.

## 5. Required wording for research claims

Preferred:

> The claim is verified relative to the declared bounded workflow, observation semantics, fault model, candidate evidence language, and external cryptographic assumptions.

Avoid:

> The formal proof proves that the empirical result is true.

The framework proves preservation, separation, sufficiency, impossibility, bounded optimality, and explicit trust contracts. It does not convert unmodeled empirical reality into a theorem.
