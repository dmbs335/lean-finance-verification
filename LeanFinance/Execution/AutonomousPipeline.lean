import LeanFinance.Execution.Ledger
import LeanFinance.Epistemic.CertificateComposition

namespace LeanFinance.Execution

/-- Digest equalities required to connect a dataset, state estimate, policy,
    shielded decision, authorization, execution, and reconciliation into one
    autonomous-control pipeline. -/
structure AutonomousPipelineBinding where
  datasetDigest : Nat
  stateDatasetDigest : Nat
  stateDigest : Nat
  decisionStateDigest : Nat
  policyDigest : Nat
  decisionPolicyDigest : Nat
  decisionDigest : Nat
  authorizationDecisionDigest : Nat
  authorizationDigest : Nat
  executionAuthorizationDigest : Nat
  executionDigest : Nat
  reconciliationExecutionDigest : Nat
  deriving Repr, DecidableEq

namespace AutonomousPipelineBinding

def bound (binding : AutonomousPipelineBinding) : Bool :=
  decide (binding.datasetDigest = binding.stateDatasetDigest) &&
    decide (binding.stateDigest = binding.decisionStateDigest) &&
      decide (binding.policyDigest = binding.decisionPolicyDigest) &&
        decide (binding.decisionDigest =
          binding.authorizationDecisionDigest) &&
          decide (binding.authorizationDigest =
            binding.executionAuthorizationDigest) &&
            decide (binding.executionDigest =
              binding.reconciliationExecutionDigest)

/-- Acceptance exposes every cross-boundary identity required by the pipeline. -/
theorem accepted_has_all_bindings
    (binding : AutonomousPipelineBinding)
    (accepted : binding.bound = true) :
    binding.datasetDigest = binding.stateDatasetDigest ∧
      binding.stateDigest = binding.decisionStateDigest ∧
        binding.policyDigest = binding.decisionPolicyDigest ∧
          binding.decisionDigest = binding.authorizationDecisionDigest ∧
            binding.authorizationDigest =
              binding.executionAuthorizationDigest ∧
              binding.executionDigest =
                binding.reconciliationExecutionDigest := by
  simp [bound] at accepted
  rcases accepted with ⟨⟨⟨⟨⟨hDataset, hState⟩, hPolicy⟩,
    hDecision⟩, hAuthorization⟩, hExecution⟩
  exact ⟨hDataset, hState, hPolicy, hDecision, hAuthorization, hExecution⟩

end AutonomousPipelineBinding

inductive AutonomousWorld where
  | matched
  | datasetSubstituted
  | stateRelabeled
  | policyRelabeled
  | authorizationSwapped
  | executionRelabeled
  | reconciliationRelabeled
  deriving Repr, DecidableEq

def localCertificatesValid (_ : AutonomousWorld) : Bool := true

def datasetStateBound : AutonomousWorld → Bool
  | .datasetSubstituted => false
  | _ => true

def stateDecisionBound : AutonomousWorld → Bool
  | .stateRelabeled => false
  | _ => true

def policyDecisionBound : AutonomousWorld → Bool
  | .policyRelabeled => false
  | _ => true

def decisionAuthorizationBound : AutonomousWorld → Bool
  | .authorizationSwapped => false
  | _ => true

def authorizationExecutionBound : AutonomousWorld → Bool
  | .executionRelabeled => false
  | _ => true

def executionReconciliationBound : AutonomousWorld → Bool
  | .reconciliationRelabeled => false
  | _ => true

def autonomousGlobalClaim (world : AutonomousWorld) : Prop :=
  localCertificatesValid world = true ∧
    datasetStateBound world = true ∧
      stateDecisionBound world = true ∧
        policyDecisionBound world = true ∧
          decisionAuthorizationBound world = true ∧
            authorizationExecutionBound world = true ∧
              executionReconciliationBound world = true

inductive AutonomousChannel where
  | localValiditySummary
  | datasetStateBindingReceipt
  | decisionInputBindingReceipt
  | decisionAuthorizationBindingReceipt
  | authorizationExecutionBindingReceipt
  | executionReconciliationBindingReceipt
  | globalAutonomousBundle
  deriving Repr, DecidableEq

def autonomousObserve :
    AutonomousChannel → AutonomousWorld → List Bool
  | .localValiditySummary, world => [localCertificatesValid world]
  | .datasetStateBindingReceipt, world => [datasetStateBound world]
  | .decisionInputBindingReceipt, world =>
      [stateDecisionBound world, policyDecisionBound world]
  | .decisionAuthorizationBindingReceipt, world =>
      [decisionAuthorizationBound world]
  | .authorizationExecutionBindingReceipt, world =>
      [authorizationExecutionBound world]
  | .executionReconciliationBindingReceipt, world =>
      [executionReconciliationBound world]
  | .globalAutonomousBundle, world =>
      [datasetStateBound world && stateDecisionBound world &&
        policyDecisionBound world && decisionAuthorizationBound world &&
        authorizationExecutionBound world &&
        executionReconciliationBound world]

def narrowAutonomousSelection (channel : AutonomousChannel) : Prop :=
  channel = .datasetStateBindingReceipt ∨
    channel = .decisionInputBindingReceipt ∨
      channel = .decisionAuthorizationBindingReceipt ∨
        channel = .authorizationExecutionBindingReceipt ∨
          channel = .executionReconciliationBindingReceipt

/-- The five narrow receipts jointly verify the seven-artifact global claim. -/
theorem narrow_autonomous_receipts_verify
    : LeanFinance.Epistemic.ChannelSelectionVerifies
        autonomousObserve narrowAutonomousSelection autonomousGlobalClaim := by
  intro left right sameEvidence
  have hDataset := sameEvidence .datasetStateBindingReceipt (by
    simp [narrowAutonomousSelection])
  have hDecisionInput := sameEvidence .decisionInputBindingReceipt (by
    simp [narrowAutonomousSelection])
  have hDecisionAuthorization :=
    sameEvidence .decisionAuthorizationBindingReceipt (by
      simp [narrowAutonomousSelection])
  have hAuthorizationExecution :=
    sameEvidence .authorizationExecutionBindingReceipt (by
      simp [narrowAutonomousSelection])
  have hExecutionReconciliation :=
    sameEvidence .executionReconciliationBindingReceipt (by
      simp [narrowAutonomousSelection])
  cases left <;> cases right <;>
    simp_all [autonomousObserve, autonomousGlobalClaim,
      localCertificatesValid, datasetStateBound, stateDecisionBound,
      policyDecisionBound, decisionAuthorizationBound,
      authorizationExecutionBound, executionReconciliationBound]

/-- Local validity alone cannot detect dataset substitution. -/
def localAutonomousCounterexample :
    LeanFinance.Epistemic.VerificationCounterexample
      (fun world => autonomousObserve .localValiditySummary world)
      autonomousGlobalClaim :=
  { left := .matched
    right := .datasetSubstituted
    sameEvidence := rfl
    leftClaim := by
      simp [autonomousGlobalClaim, localCertificatesValid,
        datasetStateBound, stateDecisionBound, policyDecisionBound,
        decisionAuthorizationBound, authorizationExecutionBound,
        executionReconciliationBound]
    rightNotClaim := by
      simp [autonomousGlobalClaim, localCertificatesValid,
        datasetStateBound, stateDecisionBound, policyDecisionBound,
        decisionAuthorizationBound, authorizationExecutionBound,
        executionReconciliationBound] }

theorem local_autonomous_certificates_do_not_compose :
    ¬ LeanFinance.Epistemic.Verifiable
      (fun world => autonomousObserve .localValiditySummary world)
      autonomousGlobalClaim :=
  localAutonomousCounterexample.notVerifiable

end LeanFinance.Execution
