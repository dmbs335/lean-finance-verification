import LeanFinance.Epistemic.ObservationBoundary

namespace LeanFinance.Epistemic.ObservationBoundaryExample

inductive History where
  | honest
  | hiddenSweep
  deriving Repr, DecidableEq

structure PublishedBoundary where
  strategyId : Nat
  resultDigest : Nat
  deriving Repr, DecidableEq

/-- Both histories expose the same publication record. -/
def publicationBoundary : History → PublishedBoundary
  | _ => { strategyId := 1, resultDigest := 42 }

inductive Channel where
  | resultBundle
  | rfc3161Timestamp
  | executionReceipt
  deriving Repr, DecidableEq

inductive Observation where
  | bundle (digest : Nat)
  | timestamped (digest : Nat)
  | executionClean
  | hiddenExecution
  deriving Repr, DecidableEq

def observe : Channel → History → Observation
  | .resultBundle, _ => .bundle 42
  | .rfc3161Timestamp, _ => .timestamped 42
  | .executionReceipt, .honest => .executionClean
  | .executionReceipt, .hiddenSweep => .hiddenExecution

def noHiddenExecution : History → Prop
  | .honest => True
  | .hiddenSweep => False

def selectedDownstream : Channel → Prop
  | .resultBundle | .rfc3161Timestamp => True
  | .executionReceipt => False

def selectedReceipt : Channel → Prop
  | .executionReceipt => True
  | _ => False

def publicationCounterexample :
    VerificationCounterexample publicationBoundary noHiddenExecution :=
  {
    left := .honest
    right := .hiddenSweep
    sameEvidence := rfl
    leftClaim := True.intro
    rightNotClaim := by simp [noHiddenExecution]
  }

theorem downstream_channels_respect_publication_boundary :
    SelectedChannelsRespectBoundary
      publicationBoundary observe selectedDownstream := by
  intro evidenceChannel chosen left right _sameBoundary
  cases evidenceChannel <;>
    simp [selectedDownstream] at chosen
  · rfl
  · rfl

theorem result_bundle_and_timestamp_cannot_verify_hidden_execution :
    ¬ ChannelSelectionVerifies
      observe selectedDownstream noHiddenExecution :=
  boundary_counterexample_refutes_selected_channels
    publicationBoundary observe selectedDownstream noHiddenExecution
    downstream_channels_respect_publication_boundary
    publicationCounterexample

/-- The execution receipt crosses the missing causal boundary and does separate
the two histories. -/
theorem execution_receipt_verifies_hidden_execution :
    ChannelSelectionVerifies
      observe selectedReceipt noHiddenExecution := by
  intro left right sameEvidence
  cases left <;> cases right
  · exact Iff.rfl
  · have impossible :=
      sameEvidence .executionReceipt (by simp [selectedReceipt])
    simp [observe] at impossible
  · have impossible :=
      sameEvidence .executionReceipt (by simp [selectedReceipt])
    simp [observe] at impossible
  · exact Iff.rfl

/-- The useful receipt is not downstream of the publication boundary: equal
publication records do not force equal execution receipts. -/
theorem execution_receipt_does_not_respect_publication_boundary :
    ¬ ChannelRespectsBoundary
      publicationBoundary observe .executionReceipt := by
  intro respects
  have sameReceipt := respects .honest .hiddenSweep rfl
  simp [observe] at sameReceipt

end LeanFinance.Epistemic.ObservationBoundaryExample
