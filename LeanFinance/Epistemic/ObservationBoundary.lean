import LeanFinance.Epistemic.Verification
import LeanFinance.Epistemic.CutSet

namespace LeanFinance.Epistemic

universe u v w x y

/-- Evidence factors through an observation boundary when it is a deterministic
    post-processing of the boundary state. -/
def FactorsThroughBoundary
    {History : Type u}
    {Boundary : Type v}
    {Evidence : Type w}
    (boundary : History → Boundary)
    (evidence : History → Evidence) : Prop :=
  ∃ postprocess : Boundary → Evidence,
    ∀ history,
      evidence history = postprocess (boundary history)

/-- If downstream evidence verifies a claim, the boundary through which that
    evidence factors already verified the claim. Deterministic downstream work
    cannot create a distinction absent at the boundary. -/
theorem verifiable_boundary_of_factored_evidence
    {History : Type u}
    {Boundary : Type v}
    {Evidence : Type w}
    (boundary : History → Boundary)
    (evidence : History → Evidence)
    (claim : History → Prop)
    (factors : FactorsThroughBoundary boundary evidence)
    (verified : Verifiable evidence claim) :
    Verifiable boundary claim := by
  rcases factors with ⟨postprocess, factor⟩
  intro left right sameBoundary
  apply verified left right
  calc
    evidence left = postprocess (boundary left) := factor left
    _ = postprocess (boundary right) :=
      congrArg postprocess sameBoundary
    _ = evidence right := (factor right).symm

/-- Downstream-evidence impossibility: if a claim is not verifiable at a
    boundary, no deterministic evidence derived solely from that boundary can
    verify it. -/
theorem downstream_evidence_impossibility
    {History : Type u}
    {Boundary : Type v}
    {Evidence : Type w}
    (boundary : History → Boundary)
    (evidence : History → Evidence)
    (claim : History → Prop)
    (factors : FactorsThroughBoundary boundary evidence)
    (notBoundaryVerifiable : ¬ Verifiable boundary claim) :
    ¬ Verifiable evidence claim := by
  intro verified
  exact notBoundaryVerifiable
    (verifiable_boundary_of_factored_evidence
      boundary evidence claim factors verified)

/-- A concrete indistinguishable boundary pair remains a counterexample after
    every factored downstream transformation. -/
def factoredEvidenceCounterexample
    {History : Type u}
    {Boundary : Type v}
    {Evidence : Type w}
    {boundary : History → Boundary}
    {evidence : History → Evidence}
    {claim : History → Prop}
    (counterexample : VerificationCounterexample boundary claim)
    (factors : FactorsThroughBoundary boundary evidence) :
    VerificationCounterexample evidence claim := by
  rcases factors with ⟨postprocess, factor⟩
  exact
    {
      left := counterexample.left
      right := counterexample.right
      sameEvidence := by
        calc
          evidence counterexample.left =
              postprocess (boundary counterexample.left) :=
            factor counterexample.left
          _ = postprocess (boundary counterexample.right) :=
            congrArg postprocess counterexample.sameEvidence
          _ = evidence counterexample.right :=
            (factor counterexample.right).symm
      leftClaim := counterexample.leftClaim
      rightNotClaim := counterexample.rightNotClaim
    }

/-- A claim decoder at the boundary is sufficient for verification. Together
    with the impossibility theorem, this isolates the exact epistemic role of a
    boundary rather than the strength of its downstream encoding. -/
theorem boundary_decoder_suffices
    {History : Type u}
    {Boundary : Type v}
    (boundary : History → Boundary)
    (claim : History → Prop)
    (decode : Boundary → Prop)
    (factor : ∀ history, claim history ↔ decode (boundary history)) :
    Verifiable boundary claim :=
  verifiable_of_decoder boundary claim decode factor

/-- Every selected evidence channel is generated from the same boundary. -/
def SelectedChannelsFactorThroughBoundary
    {History : Type u}
    {Boundary : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (boundary : History → Boundary)
    (channel : Channel → History → Observation)
    (selected : Channel → Prop) : Prop :=
  ∀ evidenceChannel,
    selected evidenceChannel →
      ∃ postprocess : Boundary → Observation,
        ∀ history,
          channel evidenceChannel history =
            postprocess (boundary history)

/-- Equal boundary states force agreement on every selected downstream channel. -/
theorem channelsAgree_of_same_boundary
    {History : Type u}
    {Boundary : Type v}
    {Channel : Type w}
    {Observation : Type x}
    {boundary : History → Boundary}
    {channel : Channel → History → Observation}
    {selected : Channel → Prop}
    (factors :
      SelectedChannelsFactorThroughBoundary
        boundary channel selected)
    {left right : History}
    (sameBoundary : boundary left = boundary right) :
    ChannelsAgree channel selected left right := by
  intro evidenceChannel chosen
  rcases factors evidenceChannel chosen with
    ⟨postprocess, factor⟩
  calc
    channel evidenceChannel left =
        postprocess (boundary left) := factor left
    _ = postprocess (boundary right) :=
      congrArg postprocess sameBoundary
    _ = channel evidenceChannel right :=
      (factor right).symm

/-- If a claim-changing history pair is silent at one boundary, every selected
    family of channels factored through that boundary fails verification. -/
theorem silent_boundary_pair_refutes_selected_channels
    {History : Type u}
    {Boundary : Type v}
    {Channel : Type w}
    {Observation : Type x}
    {boundary : History → Boundary}
    {channel : Channel → History → Observation}
    {selected : Channel → Prop}
    {claim : History → Prop}
    (factors :
      SelectedChannelsFactorThroughBoundary
        boundary channel selected)
    (left right : History)
    (sameBoundary : boundary left = boundary right)
    (claimDisagrees : ¬ (claim left ↔ claim right)) :
    ¬ ChannelSelectionVerifies channel selected claim := by
  intro verifies
  exact claimDisagrees
    (verifies left right
      (channelsAgree_of_same_boundary factors sameBoundary))

/-- A boundary counterexample directly refutes every selected downstream
    channel family factored through that boundary. -/
theorem boundary_counterexample_refutes_selected_channels
    {History : Type u}
    {Boundary : Type v}
    {Channel : Type w}
    {Observation : Type x}
    {boundary : History → Boundary}
    {channel : Channel → History → Observation}
    {selected : Channel → Prop}
    {claim : History → Prop}
    (counterexample : VerificationCounterexample boundary claim)
    (factors :
      SelectedChannelsFactorThroughBoundary
        boundary channel selected) :
    ¬ ChannelSelectionVerifies channel selected claim := by
  apply silent_boundary_pair_refutes_selected_channels
    factors counterexample.left counterexample.right
    counterexample.sameEvidence
  intro sameClaim
  exact counterexample.rightNotClaim
    (sameClaim.mp counterexample.leftClaim)

end LeanFinance.Epistemic
