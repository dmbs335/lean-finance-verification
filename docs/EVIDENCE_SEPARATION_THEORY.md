# Evidence Separation Theory

The proof-carrying backtest system can check many integrity contracts, but a stronger question comes first:

> When is a claim about a complete research history determined by the evidence that was actually preserved?

`LeanFinance/Epistemic/` formalizes that question independently of any one certificate format or cryptographic mechanism.

## 1. Histories, evidence, and claims

Let `History` denote the complete state of a research process, including events that may not appear in the final report. Let

```lean
observe : History → Evidence
claim   : History → Prop
```

be an evidence map and a proposition about the complete history.

Two histories are evidence-equivalent when they produce equal evidence:

```lean
def EvidenceEquivalent (observe) (left right) : Prop :=
  observe left = observe right
```

A claim is verifiable exactly when its truth value is constant on every evidence-equivalence class:

```lean
def Verifiable (observe) (claim) : Prop :=
  ∀ left right,
    observe left = observe right →
      (claim left ↔ claim right)
```

The repository proves that proposition-valued verifiability is equivalent to the existing `Inference.Identified` notion. Identification and verification therefore share one mathematical core: a target must factor through the available observation.

## 2. Verification non-amplification

The central theorem is:

```lean
theorem verification_non_amplification
    (verifiedAfter :
      Verifiable (fun h => postprocess (observe h)) claim) :
    Verifiable observe claim
```

A deterministic post-processing can merge evidence classes, but it cannot split one class into histories that the input did not distinguish. Its direct impossibility corollary is `no_free_verification`:

```text
not verifiable from E
⇒ not verifiable from hash(E)
⇒ not verifiable from canonicalize(E)
⇒ not verifiable from generated-proof(E)
```

This is an epistemic data-processing law. Cryptographic integrity can protect the evidence that exists; it cannot manufacture observations of events that never entered the evidence channel.

`VerificationCounterexample` is a constructive certificate of impossibility. It stores two histories, equal evidence, a proof that the claim holds in the first, and a proof that it fails in the second. The counterexample itself can be deterministically post-processed, proving that the indistinguishability survives downstream encodings.

## 3. Epistemic cut-set duality

Suppose evidence is divided into channels:

```lean
channel  : Channel → History → Observation
selected : Channel → Prop
```

`ChannelsAgree` means that two histories agree on every selected channel. `HitsEveryClaimDisagreement` means that each pair with different claim truth values is separated by at least one selected channel.

The mechanized duality theorem is:

```lean
theorem evidence_cut_set_duality :
  ChannelSelectionVerifies channel selected claim ↔
  HitsEveryClaimDisagreement channel selected claim
```

Thus evidence design is a hitting-set problem over adversarial history pairs:

```text
vertices: evidence channels
hyperedge for (H₁,H₂): channels that separate H₁ from H₂
constraint: hit every pair for which claim(H₁) ≠ claim(H₂)
```

`IsMinimalCutSet` states that a selection verifies the claim and that deleting any selected channel destroys verification. `necessary_channel_of_unique_separator` proves a useful lower-bound rule: if one disagreement pair has only one possible separator, every valid evidence design must include that separator.

This Prop-level duality is independent of a particular finite solver. A later synthesis layer can enumerate bounded adversarial histories, extract separator hyperedges, and solve minimum-cost or privacy-constrained hitting-set instances while using this theorem as the semantic correctness condition.

## 4. No self-certified completeness

`ResearchHistory` separates three things:

```lean
publicRecord   : Public
declaredTrials : List Trial
executedTrials : List Trial
```

The claim

```lean
def NoHiddenTrials (history) : Prop :=
  ∀ trial,
    trial ∈ history.executedTrials →
      trial ∈ history.declaredTrials
```

cannot be verified from a self-certified observation that contains only the public record and declared trials.

For any possible hidden trial, Lean constructs two histories:

```text
honest history:
  declared = []
  executed = []

selective history:
  declared = []
  executed = [hiddenTrial]
```

They produce equal self-certified evidence, but `NoHiddenTrials` has different truth values. The theorem is fully generic in the public-record and trial types:

```lean
theorem no_self_certified_completeness
    (publicRecord : Public)
    (hiddenTrial : Trial) :
    ¬ Verifiable selfCertifiedObserve NoHiddenTrials
```

The corollary `no_postprocess_can_self_certify_completeness` applies the non-amplification theorem to any deterministic output, including hashes, canonical bundles, signed local reports, and generated Lean terms.

This is not a claim that completeness can never be verified. It says that the missing execution event must enter through a channel outside the researcher's final declaration.

## 5. A proved minimal evidence design

The search-completeness model exposes two channels:

```text
selfReport  → public record + declared trials
executorLog → actually executed trials
```

Lean proves all three statements:

1. both channels together verify `NoHiddenTrials`;
2. every verifying channel selection must contain `executorLog`;
3. every verifying channel selection must contain `selfReport`.

Therefore:

```lean
theorem all_search_channels_form_minimal_cut_set :
  IsMinimalCutSet searchChannel (fun _ => True) NoHiddenTrials
```

The two necessity proofs use different adversarial pairs. The first holds the declaration fixed and varies execution; the second holds execution fixed and varies declaration. This is an explicit cut-set lower bound rather than an informal recommendation to log more data.

`BacktestCompleteness.lean` instantiates the theory with a public momentum result and a hidden parameter sweep. It proves that a visible bundle and a digest-like summary cannot certify complete exploration, while a declaration plus independent executor log is a minimal evidence cut set.

## 6. What is and is not established

The current formalization establishes structural results under exact evidence equality. It does not yet claim that every real research-history space has been modeled or that a particular executor is trustworthy.

The next research steps are:

1. define bounded adversarial history generators for concrete backtest workflows;
2. synthesize separator hyperedges and minimum-cost evidence selections;
3. attach costs for operational burden, privacy leakage, and external trust;
4. connect RFC 3161, transparency logs, remote executors, dataset vintages, and universe snapshots as concrete channel semantics;
5. characterize compositional verification: when certificates for sub-histories imply a certificate for the whole workflow;
6. study adaptive adversaries that choose hidden actions after observing which channels are deployed.

The intended research claim is deliberately narrower than “formal methods prove empirical truth.” The theory identifies which historical distinctions the evidence preserves, constructs counterexamples when it does not, and derives the additional channels necessary to make a claim decidable from evidence.
