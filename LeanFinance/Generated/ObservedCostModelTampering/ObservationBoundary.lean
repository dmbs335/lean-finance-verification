import LeanFinance.Epistemic.ObservationBoundary
import LeanFinance.Generated.ObservedCostModelTampering.Evidence

namespace LeanFinance.Generated.ObservedCostModelTampering.ObservationBoundary

open LeanFinance.Epistemic
open LeanFinance.Generated.ObservedCostModelTampering.Evidence

/-- The visible publication boundary: declaration state, selected result bundle,
    and external timestamp over the visible ledger. -/
structure VisiblePublicationBoundary where
  declaration : Observation
  result : Observation
  anchor : Observation
  deriving Repr, DecidableEq

def visibleBoundary (history : History) : VisiblePublicationBoundary :=
  {
    declaration := observe .selfReport history
    result := observe .resultBundle history
    anchor := observe .rfc3161Anchor history
  }

/-- Integrity of one complete history, interpreted as the generated workflow
    claim being true. -/
def IntegrityClaim (history : History) : Prop :=
  claim history = true

/-- Hidden execution, future-data access, and cost-model mutation all remain
    silent at the same visible publication boundary. -/
theorem three_upstream_attacks_are_boundary_silent :
    visibleBoundary .honest = visibleBoundary .hiddenSweep ∧
      visibleBoundary .honest = visibleBoundary .futureLeak ∧
      visibleBoundary .honest = visibleBoundary .costModelTampering := by
  decide

/-- Honest execution and cost-model tampering are observationally identical at
    the visible boundary while their integrity claims differ. -/
def visibleBoundaryCounterexample :
    VerificationCounterexample visibleBoundary IntegrityClaim :=
  {
    left := .honest
    right := .costModelTampering
    sameEvidence := by
      unfold EvidenceEquivalent
      decide
    leftClaim := by
      unfold IntegrityClaim
      decide
    rightNotClaim := by
      unfold IntegrityClaim
      decide
  }

theorem visible_boundary_cannot_verify_integrity :
    ¬ Verifiable visibleBoundary IntegrityClaim :=
  visibleBoundaryCounterexample.notVerifiable

/-- The selected result bundle is only one projection of the visible boundary. -/
def resultBundleFactorsThroughVisibleBoundary :
    FactorsThroughBoundary
      visibleBoundary (observe .resultBundle) :=
  {
    postprocess := fun boundary => boundary.result
    factor := fun _ => rfl
  }

/-- The RFC 3161 timestamp observation is also only a projection of the visible
    boundary. Its cryptographic strength authenticates the projection but does
    not recover omitted upstream events. -/
def rfc3161FactorsThroughVisibleBoundary :
    FactorsThroughBoundary
      visibleBoundary (observe .rfc3161Anchor) :=
  {
    postprocess := fun boundary => boundary.anchor
    factor := fun _ => rfl
  }

def selfReportFactorsThroughVisibleBoundary :
    FactorsThroughBoundary
      visibleBoundary (observe .selfReport) :=
  {
    postprocess := fun boundary => boundary.declaration
    factor := fun _ => rfl
  }

theorem result_bundle_cannot_certify_upstream_integrity :
    ¬ Verifiable (observe .resultBundle) IntegrityClaim :=
  downstream_evidence_impossibility
    visibleBoundary (observe .resultBundle) IntegrityClaim
    resultBundleFactorsThroughVisibleBoundary
    visible_boundary_cannot_verify_integrity

theorem rfc3161_cannot_certify_upstream_integrity :
    ¬ Verifiable (observe .rfc3161Anchor) IntegrityClaim :=
  downstream_evidence_impossibility
    visibleBoundary (observe .rfc3161Anchor) IntegrityClaim
    rfc3161FactorsThroughVisibleBoundary
    visible_boundary_cannot_verify_integrity

/-- No hash, signature, serialization, proof term, or report generated solely
    from the visible boundary can certify the omitted upstream distinction. -/
theorem no_postprocess_of_visible_boundary_can_certify_integrity
    {DownstreamEvidence : Type}
    (postprocess : VisiblePublicationBoundary → DownstreamEvidence) :
    ¬ Verifiable
      (fun history => postprocess (visibleBoundary history))
      IntegrityClaim :=
  visibleBoundaryCounterexample.postprocess_notVerifiable postprocess

/-- The three concrete publication-side channels all factor through the same
    visible boundary. -/
def visiblePublicationChannel (evidenceChannel : Channel) : Prop :=
  evidenceChannel = .selfReport ∨
    evidenceChannel = .resultBundle ∨
    evidenceChannel = .rfc3161Anchor

theorem visible_publication_channels_factor_through_boundary :
    SelectedChannelsFactorThroughBoundary
      visibleBoundary observe visiblePublicationChannel := by
  intro evidenceChannel selected
  rcases selected with rfl | rfl | rfl
  · exact
      ⟨selfReportFactorsThroughVisibleBoundary.postprocess,
        selfReportFactorsThroughVisibleBoundary.factor⟩
  · exact
      ⟨resultBundleFactorsThroughVisibleBoundary.postprocess,
        resultBundleFactorsThroughVisibleBoundary.factor⟩
  · exact
      ⟨rfc3161FactorsThroughVisibleBoundary.postprocess,
        rfc3161FactorsThroughVisibleBoundary.factor⟩

/-- Even the complete selected family of declaration, result, and timestamp
    channels cannot verify the upstream integrity claim. -/
theorem visible_publication_channel_family_cannot_verify_integrity :
    ¬ ChannelSelectionVerifies
      observe visiblePublicationChannel IntegrityClaim :=
  boundary_counterexample_refutes_selected_channels
    visibleBoundaryCounterexample
    visible_publication_channels_factor_through_boundary

end LeanFinance.Generated.ObservedCostModelTampering.ObservationBoundary
