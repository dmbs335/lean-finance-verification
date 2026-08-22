import LeanFinance.Epistemic.TransitionSeparation
import LeanFinance.Generated.ObservedCostModelTampering.CEGIS

namespace LeanFinance.Generated.ObservedCostModelTampering.TransitionSeparation

open LeanFinance.Epistemic

set_option maxRecDepth 100000
set_option maxHeartbeats 8000000

abbrev WorkflowAction :=
  LeanFinance.Generated.ObservedCostModelTampering.Search.Action
abbrev EvidenceHistory :=
  LeanFinance.Generated.ObservedCostModelTampering.Evidence.History
abbrev EvidenceChannel :=
  LeanFinance.Generated.ObservedCostModelTampering.Evidence.Channel

inductive ViolationKind where
  | undeclaredExecution
  | hiddenSweep
  | futureDataAccess
  | costModelMutation
  deriving Repr, DecidableEq

def classifyViolationAction :
    WorkflowAction → Option ViolationKind
  | .executeBaseline => some .undeclaredExecution
  | .executeHiddenSweep => some .hiddenSweep
  | .readFutureData => some .futureDataAccess
  | .tamperCostModel => some .costModelMutation
  | .declareBaseline => none
  | .publishResult => none
  | .anchorLedger => none

def firstViolationKind
    (history : EvidenceHistory) : Option ViolationKind :=
  match firstViolationAction
      LeanFinance.Generated.ObservedCostModelTampering.Search.workflow
      LeanFinance.Generated.ObservedCostModelTampering.Search.claimState
      (LeanFinance.Generated.ObservedCostModelTampering.CEGIS.historyTrace history) with
  | none => none
  | some action => classifyViolationAction action

/-- The generated model has one safe terminal history; every other terminal
    history has one of four first-violation transition kinds. -/
theorem no_first_violation_iff_honest
    (history : EvidenceHistory) :
    firstViolationKind history = none ↔
      history = .honest := by
  cases history <;> decide

theorem model_claim_iff_no_first_violation
    (history : EvidenceHistory) :
    LeanFinance.Generated.ObservedCostModelTampering.Evidence.model.ClaimHolds history ↔
      FirstViolationClaim firstViolationKind history := by
  cases history <;> decide

/-- One receipt per primitive first-violation boundary. -/
def transitionBasis : List EvidenceChannel :=
  [.selfReport,
    .targetedReceipt_executeHiddenSweep,
    .targetedReceipt_readFutureData,
    .targetedReceipt_tamperCostModel]

theorem transition_basis_is_exact_history_optimum :
    transitionBasis =
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.decode
        LeanFinance.Generated.ObservedCostModelTampering.Evidence.selected := by
  decide

theorem declaration_receipt_persistent :
    PersistentTransitionSeparator
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe
      firstViolationKind
      (.selfReport : EvidenceChannel)
      .undeclaredExecution := by
  intro safeHistory badHistory safeClass badClass
  have safeEq : safeHistory = .honest :=
    (no_first_violation_iff_honest safeHistory).mp safeClass
  subst safeHistory
  revert badClass
  cases badHistory <;> decide

theorem hidden_sweep_receipt_persistent :
    PersistentTransitionSeparator
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe
      firstViolationKind
      (.targetedReceipt_executeHiddenSweep : EvidenceChannel)
      .hiddenSweep := by
  intro safeHistory badHistory safeClass badClass
  have safeEq : safeHistory = .honest :=
    (no_first_violation_iff_honest safeHistory).mp safeClass
  subst safeHistory
  revert badClass
  cases badHistory <;> decide

theorem future_data_receipt_persistent :
    PersistentTransitionSeparator
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe
      firstViolationKind
      (.targetedReceipt_readFutureData : EvidenceChannel)
      .futureDataAccess := by
  intro safeHistory badHistory safeClass badClass
  have safeEq : safeHistory = .honest :=
    (no_first_violation_iff_honest safeHistory).mp safeClass
  subst safeHistory
  revert badClass
  cases badHistory <;> decide

theorem cost_model_receipt_persistent :
    PersistentTransitionSeparator
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe
      firstViolationKind
      (.targetedReceipt_tamperCostModel : EvidenceChannel)
      .costModelMutation := by
  intro safeHistory badHistory safeClass badClass
  have safeEq : safeHistory = .honest :=
    (no_first_violation_iff_honest safeHistory).mp safeClass
  subst safeHistory
  revert badClass
  cases badHistory <;> decide

theorem transition_basis_persistently_covers_first_violations :
    PersistentTransitionCover
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe
      (fun evidenceChannel => evidenceChannel ∈ transitionBasis)
      firstViolationKind := by
  intro violation _occurs
  cases violation with
  | undeclaredExecution =>
      exact
        ⟨.selfReport, by simp [transitionBasis],
          declaration_receipt_persistent⟩
  | hiddenSweep =>
      exact
        ⟨.targetedReceipt_executeHiddenSweep,
          by simp [transitionBasis],
          hidden_sweep_receipt_persistent⟩
  | futureDataAccess =>
      exact
        ⟨.targetedReceipt_readFutureData,
          by simp [transitionBasis],
          future_data_receipt_persistent⟩
  | costModelMutation =>
      exact
        ⟨.targetedReceipt_tamperCostModel,
          by simp [transitionBasis],
          cost_model_receipt_persistent⟩

theorem transition_basis_verifies_first_violation_absence :
    ChannelSelectionVerifies
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe
      (fun evidenceChannel => evidenceChannel ∈ transitionBasis)
      (FirstViolationClaim firstViolationKind) :=
  persistent_transition_cover_implies_verification
    transition_basis_persistently_covers_first_violations

/-- Transition-level verification is extensionally the generated integrity
    claim over all bounded histories. -/
theorem transition_basis_verifies_integrity :
    ChannelSelectionVerifies
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe
      (fun evidenceChannel => evidenceChannel ∈ transitionBasis)
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.model.ClaimHolds := by
  intro left right sameEvidence
  have transitionSame :=
    transition_basis_verifies_first_violation_absence
      left right sameEvidence
  constructor
  · intro leftClaim
    have leftSafe : FirstViolationClaim firstViolationKind left :=
      (model_claim_iff_no_first_violation left).mp leftClaim
    have rightSafe := transitionSame.mp leftSafe
    exact
      (model_claim_iff_no_first_violation right).mpr rightSafe
  · intro rightClaim
    have rightSafe : FirstViolationClaim firstViolationKind right :=
      (model_claim_iff_no_first_violation right).mp rightClaim
    have leftSafe := transitionSame.mpr rightSafe
    exact
      (model_claim_iff_no_first_violation left).mpr leftSafe

/-- Publication-side declaration/result/timestamp evidence is silent on the
    cost-model first-violation transition. -/
def publicationChannel (evidenceChannel : EvidenceChannel) : Prop :=
  evidenceChannel = .selfReport ∨
    evidenceChannel = .resultBundle ∨
    evidenceChannel = .rfc3161Anchor

def publicationSilentWitness :
    SilentFirstViolationWitness
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe
      publicationChannel firstViolationKind :=
  {
    safeHistory := .honest
    badHistory := .costModelTampering
    violation := .costModelMutation
    safeClass := by decide
    badClass := by decide
    selectedAgree := by
      intro evidenceChannel selected
      rcases selected with rfl | rfl | rfl <;> decide
  }

theorem publication_channels_cannot_verify_first_violation_absence :
    ¬ ChannelSelectionVerifies
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe
      publicationChannel
      (FirstViolationClaim firstViolationKind) :=
  publicationSilentWitness.silent_first_violation_implies_unverifiable

def violatingHistories : List EvidenceHistory :=
  LeanFinance.Generated.ObservedCostModelTampering.Evidence.histories.filter
    (fun history =>
      !(LeanFinance.Generated.ObservedCostModelTampering.Evidence.claim history))

def primitiveViolationKinds : List ViolationKind :=
  [.undeclaredExecution,
    .hiddenSweep,
    .futureDataAccess,
    .costModelMutation]

theorem terminal_disagreement_pair_count :
    violatingHistories.length = 31 := by
  decide

theorem primitive_transition_obligation_count :
    primitiveViolationKinds.length = 4 := by
  decide

theorem transition_obligations_strictly_compress_terminal_pairs :
    primitiveViolationKinds.length < violatingHistories.length := by
  decide

end LeanFinance.Generated.ObservedCostModelTampering.TransitionSeparation
