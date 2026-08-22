import LeanFinance.Inference.Identification

namespace LeanFinance.Epistemic

universe u v w x

/-- Two complete histories are evidence-equivalent when the selected
    observation map cannot distinguish them. -/
def EvidenceEquivalent
    {History : Type u}
    {Evidence : Type v}
    (observe : History → Evidence)
    (left right : History) : Prop :=
  observe left = observe right

/-- A claim is verifiable from an evidence map exactly when its truth value is
    constant on every evidence-equivalence class. -/
def Verifiable
    {History : Type u}
    {Evidence : Type v}
    (observe : History → Evidence)
    (claim : History → Prop) : Prop :=
  ∀ left right,
    EvidenceEquivalent observe left right →
      (claim left ↔ claim right)

theorem evidenceEquivalent_refl
    {History : Type u}
    {Evidence : Type v}
    (observe : History → Evidence)
    (history : History) :
    EvidenceEquivalent observe history history :=
  rfl

theorem evidenceEquivalent_symm
    {History : Type u}
    {Evidence : Type v}
    {observe : History → Evidence}
    {left right : History}
    (same : EvidenceEquivalent observe left right) :
    EvidenceEquivalent observe right left :=
  same.symm

theorem evidenceEquivalent_trans
    {History : Type u}
    {Evidence : Type v}
    {observe : History → Evidence}
    {first second third : History}
    (firstSecond : EvidenceEquivalent observe first second)
    (secondThird : EvidenceEquivalent observe second third) :
    EvidenceEquivalent observe first third :=
  firstSecond.trans secondThird

/-- Epistemic verifiability is the proposition-valued specialization of the
    repository's existing identification notion. -/
theorem verifiable_implies_identified
    {History : Type u}
    {Evidence : Type v}
    (observe : History → Evidence)
    (claim : History → Prop)
    (verifiable : Verifiable observe claim) :
    Inference.Identified observe claim := by
  intro left right sameEvidence
  exact propext (verifiable left right sameEvidence)

theorem identified_implies_verifiable
    {History : Type u}
    {Evidence : Type v}
    (observe : History → Evidence)
    (claim : History → Prop)
    (identified : Inference.Identified observe claim) :
    Verifiable observe claim := by
  intro left right sameEvidence
  have sameClaim : claim left = claim right :=
    identified left right sameEvidence
  exact Iff.of_eq sameClaim

theorem verifiable_iff_identified
    {History : Type u}
    {Evidence : Type v}
    (observe : History → Evidence)
    (claim : History → Prop) :
    Verifiable observe claim ↔
      Inference.Identified observe claim :=
  ⟨verifiable_implies_identified observe claim,
    identified_implies_verifiable observe claim⟩

/-- A decoder from evidence to the claim supplies a sufficient verification
    procedure. -/
theorem verifiable_of_decoder
    {History : Type u}
    {Evidence : Type v}
    (observe : History → Evidence)
    (claim : History → Prop)
    (decode : Evidence → Prop)
    (factor : ∀ history, claim history ↔ decode (observe history)) :
    Verifiable observe claim := by
  intro left right sameEvidence
  constructor
  · intro leftClaim
    apply (factor right).mpr
    have decodedLeft : decode (observe left) :=
      (factor left).mp leftClaim
    rw [sameEvidence] at decodedLeft
    exact decodedLeft
  · intro rightClaim
    apply (factor left).mpr
    have decodedRight : decode (observe right) :=
      (factor right).mp rightClaim
    rw [← sameEvidence] at decodedRight
    exact decodedRight

/-- Verification non-amplification: if a deterministic post-processing of the
    evidence verifies a claim, the original evidence already verified it. -/
theorem verification_non_amplification
    {History : Type u}
    {Evidence : Type v}
    {Output : Type w}
    (observe : History → Evidence)
    (postprocess : Evidence → Output)
    (claim : History → Prop)
    (verifiedAfter :
      Verifiable (fun history => postprocess (observe history)) claim) :
    Verifiable observe claim := by
  intro left right sameEvidence
  apply verifiedAfter left right
  exact congrArg postprocess sameEvidence

/-- No-free-verification principle: deterministic hashing, serialization,
    reporting, or proof-generation cannot make an unverifiable claim
    verifiable after the fact. -/
theorem no_free_verification
    {History : Type u}
    {Evidence : Type v}
    {Output : Type w}
    (observe : History → Evidence)
    (postprocess : Evidence → Output)
    (claim : History → Prop)
    (notVerifiable : ¬ Verifiable observe claim) :
    ¬ Verifiable (fun history => postprocess (observe history)) claim := by
  intro verifiedAfter
  exact notVerifiable
    (verification_non_amplification observe postprocess claim verifiedAfter)

/-- Adding genuinely finer evidence cannot destroy verifiability. -/
theorem verifiable_of_refinement
    {History : Type u}
    {CoarseEvidence : Type v}
    {FineEvidence : Type w}
    (coarse : History → CoarseEvidence)
    (fine : History → FineEvidence)
    (forget : FineEvidence → CoarseEvidence)
    (claim : History → Prop)
    (refines : ∀ history, coarse history = forget (fine history))
    (verifiedCoarse : Verifiable coarse claim) :
    Verifiable fine claim := by
  intro left right sameFine
  apply verifiedCoarse left right
  change coarse left = coarse right
  calc
    coarse left = forget (fine left) := refines left
    _ = forget (fine right) := congrArg forget sameFine
    _ = coarse right := (refines right).symm

/-- A constructive witness that one evidence map cannot verify one claim. -/
structure VerificationCounterexample
    {History : Type u}
    {Evidence : Type v}
    (observe : History → Evidence)
    (claim : History → Prop) where
  left : History
  right : History
  sameEvidence : EvidenceEquivalent observe left right
  leftClaim : claim left
  rightNotClaim : ¬ claim right

namespace VerificationCounterexample

theorem notVerifiable
    {History : Type u}
    {Evidence : Type v}
    {observe : History → Evidence}
    {claim : History → Prop}
    (counterexample : VerificationCounterexample observe claim) :
    ¬ Verifiable observe claim := by
  intro verified
  exact counterexample.rightNotClaim
    ((verified counterexample.left counterexample.right
      counterexample.sameEvidence).mp counterexample.leftClaim)

/-- Deterministic post-processing preserves an indistinguishable
    counterexample. -/
def postprocess
    {History : Type u}
    {Evidence : Type v}
    {Output : Type w}
    {observe : History → Evidence}
    {claim : History → Prop}
    (counterexample : VerificationCounterexample observe claim)
    (transform : Evidence → Output) :
    VerificationCounterexample
      (fun history => transform (observe history)) claim :=
  {
    left := counterexample.left
    right := counterexample.right
    sameEvidence := congrArg transform counterexample.sameEvidence
    leftClaim := counterexample.leftClaim
    rightNotClaim := counterexample.rightNotClaim
  }

theorem postprocess_notVerifiable
    {History : Type u}
    {Evidence : Type v}
    {Output : Type w}
    {observe : History → Evidence}
    {claim : History → Prop}
    (counterexample : VerificationCounterexample observe claim)
    (transform : Evidence → Output) :
    ¬ Verifiable (fun history => transform (observe history)) claim :=
  (counterexample.postprocess transform).notVerifiable

end VerificationCounterexample

end LeanFinance.Epistemic
