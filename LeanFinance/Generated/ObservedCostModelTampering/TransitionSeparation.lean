import LeanFinance.Epistemic.TransitionSeparation
import LeanFinance.Generated.ObservedCostModelTampering.CEGIS

namespace LeanFinance.Generated.ObservedCostModelTampering.TransitionSeparation

open LeanFinance.Epistemic
namespace Search :=
  LeanFinance.Generated.ObservedCostModelTampering.Search
namespace Evidence :=
  LeanFinance.Generated.ObservedCostModelTampering.Evidence
namespace CEGIS :=
  LeanFinance.Generated.ObservedCostModelTampering.CEGIS

inductive ViolationKind where
  | undeclaredExecution
  | hiddenSweep
  | futureDataAccess
  | costModelMutation
  deriving Repr, DecidableEq

def classifyViolationAction :
    Search.Action → Option ViolationKind
  | .executeBaseline => some .undeclaredExecution
  | .executeHiddenSweep => some .hiddenSweep
  | .readFutureData => some .futureDataAccess
  | .tamperCostModel => some .costModelMutation
  | .declareBaseline => none
  | .publishResult => none
  | .anchorLedger => none

def firstViolationKind
    (history : Evidence.History) : Option ViolationKind :=
  match firstViolationAction
      Search.workflow Search.claimState
      (CEGIS.historyTrace history) with
  | none => none
  | some action => classifyViolationAction action

/-- The generated model has one safe terminal history; every other terminal
    history has one of four first-violation transition kinds. -/
theorem no_first_violation_iff_honest
    (history : Evidence.History) :
    firstViolationKind history = none ↔
      history = .honest := by
  cases history <;> decide

theorem model_claim_iff_no_first_violation
    (history : Evidence.History) :
    Evidence.model.ClaimHolds history ↔
      FirstViolationClaim firstViolationKind history := by
  cases history <;> decide

/-- One receipt per primitive first-violation boundary. -/
def transitionBasis : List Evidence.Channel :=
  [.selfReport,
    .targetedReceipt_executeHiddenSweep,
    .targetedReceipt_readFutureData,
    .targetedReceipt_tamperCostModel]

theorem transition_basis_is_exact_history_optimum :
    transitionBasis = Evidence.decode Evidence.selected := by
  decide

theorem declaration_receipt_persistent :
    PersistentTransitionSeparator
      Evidence.observe firstViolationKind
      .selfReport .undeclaredExecution := by
  intro safeHistory badHistory safeClass badClass
  have safeEq : safeHistory = .honest :=
    (no_first_violation_iff_honest safeHistory).mp safeClass
  subst safeHistory
  cases badHistory <;> decide

theorem hidden_sweep_receipt_persistent :
    PersistentTransitionSeparator
      Evidence.observe firstViolationKind
      .targetedReceipt_executeHiddenSweep .hiddenSweep := by
  intro safeHistory badHistory safeClass badClass
  have safeEq : safeHistory = .honest :=
    (no_first_violation_iff_honest safeHistory).mp safeClass
  subst safeHistory
  cases badHistory <;> decide

theorem future_data_receipt_persistent :
    PersistentTransitionSeparator
      Evidence.observe firstViolationKind
      .targetedReceipt_readFutureData .futureDataAccess := by
  intro safeHistory badHistory safeClass badClass
  have safeEq : safeHistory = .honest :=
    (no_first_violation_iff_honest safeHistory).mp safeClass
  subst safeHistory
  cases badHistory <;> decide

theorem cost_model_receipt_persistent :
    PersistentTransitionSeparator
      Evidence.observe firstViolationKind
      .targetedReceipt_tamperCostModel .costModelMutation := by
  intro safeHistory badHistory safeClass badClass
  have safeEq : safeHistory = .honest :=
    (no_first_violation_iff_honest safeHistory).mp safeClass
  subst safeHistory
  cases badHistory <;> decide

theorem transition_basis_persistently_covers_first_violations :
    PersistentTransitionCover
      Evidence.observe
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
      Evidence.observe
      (fun evidenceChannel => evidenceChannel ∈ transitionBasis)
      (FirstViolationClaim firstViolationKind) :=
  persistent_transition_cover_implies_verification
    transition_basis_persistently_covers_first_violations

/-- Transition-level verification is extensionally the generated integrity
    claim over all bounded histories. -/
theorem transition_basis_verifies_integrity :
    ChannelSelectionVerifies
      Evidence.observe
      (fun evidenceChannel => evidenceChannel ∈ transitionBasis)
      Evidence.model.ClaimHolds := by
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
def publicationChannel (evidenceChannel : Evidence.Channel) : Prop :=
  evidenceChannel = .selfReport ∨
    evidenceChannel = .resultBundle ∨
    evidenceChannel = .rfc3161Anchor

def publicationSilentWitness :
    SilentFirstViolationWitness
      Evidence.observe publicationChannel firstViolationKind :=
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
      Evidence.observe publicationChannel
      (FirstViolationClaim firstViolationKind) :=
  publicationSilentWitness.silent_first_violation_implies_unverifiable

def violatingHistories : List Evidence.History :=
  Evidence.histories.filter (fun history => !(Evidence.claim history))

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
