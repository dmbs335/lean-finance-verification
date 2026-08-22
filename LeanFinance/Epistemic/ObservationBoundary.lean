import LeanFinance.Epistemic.Verification
import LeanFinance.Epistemic.CutSet

namespace LeanFinance.Epistemic

universe u v w x y

/-- One evidence map factors through an observation boundary when all evidence
    can be computed from the boundary state alone. -/
def FactorsThroughBoundary
    {History : Type u}
    {Boundary : Type v}
    {Evidence : Type w}
    (boundary : History → Boundary)
    (evidence : History → Evidence) : Prop :=
  ∃ downstream : Boundary → Evidence,
    ∀ history,
      evidence history = downstream (boundary history)

/-- Boundary factorization is transitive along a downstream processing chain. -/
theorem factorsThroughBoundary_trans
    {History : Type u}
    {Boundary : Type v}
    {Middle : Type w}
    {Evidence : Type x}
    (boundary : History → Boundary)
    (middle : History → Middle)
    (evidence : History → Evidence)
    (middleFactors : FactorsThroughBoundary boundary middle)
    (evidenceFactors : FactorsThroughBoundary middle evidence) :
    FactorsThroughBoundary boundary evidence := by
  rcases middleFactors with ⟨middlePostprocess, middleFactor⟩
  rcases evidenceFactors with ⟨evidencePostprocess, evidenceFactor⟩
  refine ⟨fun boundaryState =>
    evidencePostprocess (middlePostprocess boundaryState), ?_⟩
  intro history
  calc
    evidence history = evidencePostprocess (middle history) :=
      evidenceFactor history
    _ = evidencePostprocess
          (middlePostprocess (boundary history)) := by
      rw [middleFactor history]

/-- Equal boundary states force equal downstream evidence for every factorized
    evidence map. -/
theorem equal_boundary_implies_equal_evidence
    {History : Type u}
    {Boundary : Type v}
    {Evidence : Type w}
    (boundary : History → Boundary)
    (evidence : History → Evidence)
    (factors : FactorsThroughBoundary boundary evidence)
    {left right : History}
    (sameBoundary : boundary left = boundary right) :
    evidence left = evidence right := by
  rcases factors with ⟨downstream, factor⟩
  calc
    evidence left = downstream (boundary left) := factor left
    _ = downstream (boundary right) :=
      congrArg downstream sameBoundary
    _ = evidence right := (factor right).symm

/-- **Downstream evidence impossibility.** If a claim is not verifiable from a
    boundary state, no deterministic evidence that factors through that
    boundary can make it verifiable. -/
theorem boundary_unverifiable_implies_downstream_unverifiable
    {History : Type u}
    {Boundary : Type v}
    {Evidence : Type w}
    (boundary : History → Boundary)
    (evidence : History → Evidence)
    (claim : History → Prop)
    (factors : FactorsThroughBoundary boundary evidence)
    (boundaryInsufficient : ¬ Verifiable boundary claim) :
    ¬ Verifiable evidence claim := by
  intro evidenceVerifies
  apply boundaryInsufficient
  intro left right sameBoundary
  exact evidenceVerifies left right
    (equal_boundary_implies_equal_evidence
      boundary evidence factors sameBoundary)

/-- A concrete indistinguishable pair at one boundary is enough to refute every
    downstream evidence map that factors through it. -/
theorem silent_boundary_pair_implies_downstream_unverifiable
    {History : Type u}
    {Boundary : Type v}
    {Evidence : Type w}
    (boundary : History → Boundary)
    (evidence : History → Evidence)
    (claim : History → Prop)
    (factors : FactorsThroughBoundary boundary evidence)
    (left right : History)
    (sameBoundary : boundary left = boundary right)
    (leftClaim : claim left)
    (rightNotClaim : ¬ claim right) :
    ¬ Verifiable evidence claim := by
  apply VerificationCounterexample.notVerifiable
  exact {
    left := left
    right := right
    sameEvidence :=
      equal_boundary_implies_equal_evidence
        boundary evidence factors sameBoundary
    leftClaim := leftClaim
    rightNotClaim := rightNotClaim
  }

/-- A selected evidence-channel family factors through one common boundary when
    each selected channel has a downstream decoder from the same boundary
    state. -/
def SelectedChannelsFactorThroughBoundary
    {Channel : Type u}
    {History : Type v}
    {Boundary : Type w}
    {Observation : Type x}
    (boundary : History → Boundary)
    (channel : Channel → History → Observation)
    (selected : Channel → Prop) : Prop :=
  ∃ downstream : Channel → Boundary → Observation,
    ∀ evidenceChannel,
      selected evidenceChannel →
        ∀ history,
          channel evidenceChannel history =
            downstream evidenceChannel (boundary history)

/-- Histories equal at the shared boundary agree on every selected factorized
    channel. -/
theorem channelsAgree_of_equal_factorized_boundary
    {Channel : Type u}
    {History : Type v}
    {Boundary : Type w}
    {Observation : Type x}
    (boundary : History → Boundary)
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (factors :
      SelectedChannelsFactorThroughBoundary
        boundary channel selected)
    {left right : History}
    (sameBoundary : boundary left = boundary right) :
    ChannelsAgree channel selected left right := by
  rcases factors with ⟨downstream, factor⟩
  intro evidenceChannel selectedChannel
  calc
    channel evidenceChannel left =
        downstream evidenceChannel (boundary left) :=
      factor evidenceChannel selectedChannel left
    _ = downstream evidenceChannel (boundary right) :=
      congrArg (downstream evidenceChannel) sameBoundary
    _ = channel evidenceChannel right :=
      (factor evidenceChannel selectedChannel right).symm

/-- **Selected downstream-channel impossibility.** If two histories cross the
    same visible boundary state but disagree on the claim, no selected family
    whose observations all factor through that boundary can verify the claim. -/
theorem silent_boundary_pair_refutes_selected_channels
    {Channel : Type u}
    {History : Type v}
    {Boundary : Type w}
    {Observation : Type x}
    (boundary : History → Boundary)
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (factors :
      SelectedChannelsFactorThroughBoundary
        boundary channel selected)
    (left right : History)
    (sameBoundary : boundary left = boundary right)
    (claimDifferent : ¬ (claim left ↔ claim right)) :
    ¬ ChannelSelectionVerifies channel selected claim := by
  intro verifies
  exact claimDifferent
    (verifies left right
      (channelsAgree_of_equal_factorized_boundary
        boundary channel selected factors sameBoundary))

/-- A downstream transformation of already factorized evidence remains
    factorized through the same boundary. This includes hashing, canonical
    serialization, signatures, report generation, and generated proof terms. -/
theorem postprocess_preserves_boundary_factorization
    {History : Type u}
    {Boundary : Type v}
    {Evidence : Type w}
    {Output : Type x}
    (boundary : History → Boundary)
    (evidence : History → Evidence)
    (postprocess : Evidence → Output)
    (factors : FactorsThroughBoundary boundary evidence) :
    FactorsThroughBoundary boundary
      (fun history => postprocess (evidence history)) := by
  rcases factors with ⟨downstream, factor⟩
  refine ⟨fun boundaryState =>
    postprocess (downstream boundaryState), ?_⟩
  intro history
  rw [factor history]

end LeanFinance.Epistemic
