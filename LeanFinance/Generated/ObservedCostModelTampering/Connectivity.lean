import LeanFinance.Epistemic.Connectivity
import LeanFinance.Generated.ObservedCostModelTampering.Evidence

namespace LeanFinance.Generated.ObservedCostModelTampering.Connectivity

open LeanFinance.Epistemic
open LeanFinance.Generated.ObservedCostModelTampering.Evidence

/-- The current minimum-cost selection has one separator for the cost-model
    mutation and is therefore a single point of failure. -/
def currentSelection : List Channel :=
  [.selfReport,
    .targetedReceipt_executeHiddenSweep,
    .targetedReceipt_readFutureData,
    .targetedReceipt_tamperCostModel]

theorem currentSelection_is_generated_optimum :
    currentSelection = decode selected := by
  decide

inductive CurrentFailure where
  | tamperReceiptLost
  deriving Repr, DecidableEq

def currentSurvives : CurrentFailure → Channel → Bool
  | .tamperReceiptLost, .targetedReceipt_tamperCostModel => false
  | .tamperReceiptLost, _ => true

def currentFailureCounterexample :
    BoundedCounterexample model
      (survivingChannels currentSelection currentSurvives
        .tamperReceiptLost) :=
  {
    left := .honest
    right := .costModelTampering
    leftMember := by simp [model, histories]
    rightMember := by simp [model, histories]
    claimDifferent := by simp [model, claim]
    selectedAgree := by
      intro evidenceChannel member
      cases evidenceChannel <;>
        simp [survivingChannels, currentSelection,
          currentSurvives, model, observe] at member ⊢
  }

theorem current_optimum_is_not_one_channel_resilient :
    ¬ FailureRobustBoundedVerifies
      model currentSelection currentSurvives := by
  intro robust
  exact currentFailureCounterexample.notBoundedVerifies
    (robust .tamperReceiptLost)

/-- Add independent backups for the two boundaries that otherwise have unique
    separators: declaration and cost-model control-plane mutation. -/
inductive ResilientChannel where
  | base (channel : Channel)
  | backupDeclaration
  | backupTamperReceipt
  deriving Repr, DecidableEq

def resilientObserve : ResilientChannel → History → Observation
  | .base evidenceChannel, history =>
      observe evidenceChannel history
  | .backupDeclaration, history =>
      observe .selfReport history
  | .backupTamperReceipt, history =>
      observe .targetedReceipt_tamperCostModel history

def resilientCost : ResilientChannel → Nat
  | .base evidenceChannel => cost evidenceChannel
  | .backupDeclaration => 3
  | .backupTamperReceipt => 3

def resilientChannels : List ResilientChannel :=
  [.base .selfReport,
    .base .resultBundle,
    .base .rfc3161Anchor,
    .base .fullExecutorLog,
    .base .targetedReceipt_executeHiddenSweep,
    .base .targetedReceipt_readFutureData,
    .base .targetedReceipt_tamperCostModel,
    .backupDeclaration,
    .backupTamperReceipt]

def resilientModel :
    BoundedEvidenceModel History ResilientChannel Observation :=
  {
    histories := histories
    channels := resilientChannels
    observe := resilientObserve
    claim := claim
    cost := resilientCost
  }

/-- This selection gives every primitive integrity boundary two independently
    removable channel witnesses. -/
def resilientSelection : List ResilientChannel :=
  [.base .selfReport,
    .backupDeclaration,
    .base .targetedReceipt_executeHiddenSweep,
    .base .targetedReceipt_readFutureData,
    .base .fullExecutorLog,
    .base .targetedReceipt_tamperCostModel,
    .backupTamperReceipt]

theorem resilient_selection_cost :
    selectionCost resilientModel resilientSelection = 20 := by
  decide

inductive SingleChannelFailure where
  | none
  | selfReport
  | backupDeclaration
  | hiddenReceipt
  | futureReceipt
  | fullExecutorLog
  | tamperReceipt
  | backupTamperReceipt
  deriving Repr, DecidableEq

def failedChannel : SingleChannelFailure → Option ResilientChannel
  | .none => none
  | .selfReport => some (.base .selfReport)
  | .backupDeclaration => some .backupDeclaration
  | .hiddenReceipt =>
      some (.base .targetedReceipt_executeHiddenSweep)
  | .futureReceipt =>
      some (.base .targetedReceipt_readFutureData)
  | .fullExecutorLog => some (.base .fullExecutorLog)
  | .tamperReceipt =>
      some (.base .targetedReceipt_tamperCostModel)
  | .backupTamperReceipt => some .backupTamperReceipt

def survivesSingleChannelFailure
    (failure : SingleChannelFailure)
    (evidenceChannel : ResilientChannel) : Bool :=
  match failedChannel failure with
  | none => true
  | some failed => decide (evidenceChannel ≠ failed)

theorem resilient_selection_survives_any_single_channel_failure :
    FailureRobustBoundedVerifies
      resilientModel resilientSelection
      survivesSingleChannelFailure := by
  intro failure
  cases failure <;>
    apply boundedVerifiesBool_sound <;>
    decide

theorem resilient_selection_semantically_survives_any_single_failure :
    ∀ failure,
      ChannelSelectionVerifies resilientModel.observe
        (fun evidenceChannel =>
          evidenceChannel ∈ survivingChannels
            resilientSelection survivesSingleChannelFailure failure)
        resilientModel.ClaimHolds :=
  failure_robust_bounded_semantically_sound
    resilientModel resilientSelection
    survivesSingleChannelFailure
    (by
      intro history
      cases history <;>
        simp [resilientModel, histories])
    resilient_selection_survives_any_single_channel_failure

/-- Independent operational trust domains. Targeted execution receipts share a
    domain, but the full executor audit is independent; declaration and tamper
    receipts each have independent backups. -/
inductive TrustDomain where
  | declarationPrimary
  | declarationBackup
  | targetedExecution
  | fullExecutionAudit
  | controlPrimary
  | controlBackup
  | publication
  deriving Repr, DecidableEq

def independentDomain : ResilientChannel → TrustDomain
  | .base .selfReport => .declarationPrimary
  | .base .resultBundle => .publication
  | .base .rfc3161Anchor => .publication
  | .base .fullExecutorLog => .fullExecutionAudit
  | .base .targetedReceipt_executeHiddenSweep => .targetedExecution
  | .base .targetedReceipt_readFutureData => .targetedExecution
  | .base .targetedReceipt_tamperCostModel => .controlPrimary
  | .backupDeclaration => .declarationBackup
  | .backupTamperReceipt => .controlBackup

theorem resilient_selection_survives_any_single_domain_failure :
    FailureRobustBoundedVerifies
      resilientModel resilientSelection
      (survivesDomainFailure independentDomain) := by
  intro failure
  cases failure with
  | none =>
      apply boundedVerifiesBool_sound
      decide
  | some failedDomain =>
      cases failedDomain <;>
        apply boundedVerifiesBool_sound <;>
        decide

/-- Merely duplicating evidence does not create independent connectivity when
    both copies remain in one compromise domain. -/
inductive CorrelatedDomain where
  | declaration
  | execution
  | control
  | publication
  deriving Repr, DecidableEq

def correlatedDomain : ResilientChannel → CorrelatedDomain
  | .base .selfReport => .declaration
  | .base .resultBundle => .publication
  | .base .rfc3161Anchor => .publication
  | .base .fullExecutorLog => .execution
  | .base .targetedReceipt_executeHiddenSweep => .execution
  | .base .targetedReceipt_readFutureData => .execution
  | .base .targetedReceipt_tamperCostModel => .control
  | .backupDeclaration => .declaration
  | .backupTamperReceipt => .control

def correlatedControlCounterexample :
    BoundedCounterexample resilientModel
      (survivingChannels resilientSelection
        (survivesDomainFailure correlatedDomain)
        (some .control)) :=
  {
    left := .honest
    right := .costModelTampering
    leftMember := by simp [resilientModel, histories]
    rightMember := by simp [resilientModel, histories]
    claimDifferent := by simp [resilientModel, claim]
    selectedAgree := by
      intro evidenceChannel member
      cases evidenceChannel with
      | base original =>
          cases original <;>
            simp [survivingChannels, resilientSelection,
              survivesDomainFailure, correlatedDomain,
              resilientModel, resilientObserve, observe]
              at member ⊢
      | backupDeclaration =>
          simp [survivingChannels, resilientSelection,
            survivesDomainFailure, correlatedDomain,
            resilientModel, resilientObserve, observe]
            at member ⊢
      | backupTamperReceipt =>
          simp [survivingChannels, resilientSelection,
            survivesDomainFailure, correlatedDomain,
            resilientModel, resilientObserve, observe]
            at member ⊢
  }

theorem same_domain_duplicates_do_not_survive_domain_compromise :
    ¬ FailureRobustBoundedVerifies
      resilientModel resilientSelection
      (survivesDomainFailure correlatedDomain) := by
  intro robust
  exact correlatedControlCounterexample.notBoundedVerifies
    (robust (some .control))

end LeanFinance.Generated.ObservedCostModelTampering.Connectivity
