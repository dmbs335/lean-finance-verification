import LeanFinance.Epistemic.RobustSynthesis
import LeanFinance.Generated.ObservedCostModelTampering.Connectivity

namespace LeanFinance.Generated.ObservedCostModelTampering.RobustSynthesis

open LeanFinance.Epistemic
open LeanFinance.Generated.ObservedCostModelTampering.Evidence
open LeanFinance.Generated.ObservedCostModelTampering.Connectivity

set_option maxRecDepth 100000
set_option maxHeartbeats 8000000

/-- Every subset of the nine-channel robust candidate language. -/
abbrev RobustCandidate := Fin 512

def robustDecodeMask (mask : Nat) : List ResilientChannel :=
  (if bitSelected mask 0 then [.base .selfReport] else [])
    ++ (if bitSelected mask 1 then [.base .resultBundle] else [])
    ++ (if bitSelected mask 2 then [.base .rfc3161Anchor] else [])
    ++ (if bitSelected mask 3 then [.base .fullExecutorLog] else [])
    ++ (if bitSelected mask 4 then
          [.base .targetedReceipt_executeHiddenSweep] else [])
    ++ (if bitSelected mask 5 then
          [.base .targetedReceipt_readFutureData] else [])
    ++ (if bitSelected mask 6 then
          [.base .targetedReceipt_tamperCostModel] else [])
    ++ (if bitSelected mask 7 then [.backupDeclaration] else [])
    ++ (if bitSelected mask 8 then [.backupTamperReceipt] else [])

def robustDecode (candidate : RobustCandidate) : List ResilientChannel :=
  robustDecodeMask candidate.val

def robustSelected : RobustCandidate :=
  ⟨505, by decide⟩

/-- Canonical bit-order rendering of the seven-channel robust architecture. -/
theorem robustSelected_decodes_to_canonical_architecture :
    robustDecode robustSelected =
      [.base .selfReport,
        .base .fullExecutorLog,
        .base .targetedReceipt_executeHiddenSweep,
        .base .targetedReceipt_readFutureData,
        .base .targetedReceipt_tamperCostModel,
        .backupDeclaration,
        .backupTamperReceipt] := by
  decide

theorem robustSelected_cost :
    selectionCost resilientModel (robustDecode robustSelected) = 20 := by
  decide

/-- No failure plus loss of each one of the nine candidate channels. -/
inductive AllSingleChannelFailure where
  | noFailure
  | selfReport
  | resultBundle
  | rfc3161Anchor
  | fullExecutorLog
  | hiddenReceipt
  | futureReceipt
  | tamperReceipt
  | backupDeclaration
  | backupTamperReceipt
  deriving Repr, DecidableEq

def failedChannel :
    AllSingleChannelFailure → Option ResilientChannel
  | .noFailure => none
  | .selfReport => some (.base .selfReport)
  | .resultBundle => some (.base .resultBundle)
  | .rfc3161Anchor => some (.base .rfc3161Anchor)
  | .fullExecutorLog => some (.base .fullExecutorLog)
  | .hiddenReceipt =>
      some (.base .targetedReceipt_executeHiddenSweep)
  | .futureReceipt =>
      some (.base .targetedReceipt_readFutureData)
  | .tamperReceipt =>
      some (.base .targetedReceipt_tamperCostModel)
  | .backupDeclaration => some .backupDeclaration
  | .backupTamperReceipt => some .backupTamperReceipt

def survivesAllSingleChannelFailure
    (failure : AllSingleChannelFailure)
    (evidenceChannel : ResilientChannel) : Bool :=
  match failedChannel failure with
  | none => true
  | some failed => decide (evidenceChannel ≠ failed)

def allSingleChannelFailures : List AllSingleChannelFailure :=
  [.noFailure,
    .selfReport,
    .resultBundle,
    .rfc3161Anchor,
    .fullExecutorLog,
    .hiddenReceipt,
    .futureReceipt,
    .tamperReceipt,
    .backupDeclaration,
    .backupTamperReceipt]

theorem allSingleChannelFailures_complete
    (failure : AllSingleChannelFailure) :
    failure ∈ allSingleChannelFailures := by
  cases failure <;> simp [allSingleChannelFailures]

theorem robustSelected_verifies_all_single_channel_failures_on_list :
    FailureRobustBoundedVerifiesOn
      resilientModel
      (robustDecode robustSelected)
      allSingleChannelFailures
      survivesAllSingleChannelFailure := by
  apply robustBoundedVerifiesBool_sound
  decide

theorem robustSelected_survives_any_single_channel_failure :
    FailureRobustBoundedVerifies
      resilientModel
      (robustDecode robustSelected)
      survivesAllSingleChannelFailure :=
  failure_list_complete_implies_full_robustness
    resilientModel
    (robustDecode robustSelected)
    allSingleChannelFailures
    survivesAllSingleChannelFailure
    allSingleChannelFailures_complete
    robustSelected_verifies_all_single_channel_failures_on_list

/-- Kernel computation checks all 512 channel subsets and all ten single-channel
    failure scenarios. -/
theorem singleChannelCheckerCostMinimal :
    ∀ candidate : RobustCandidate,
      robustBoundedVerifiesBool
          resilientModel
          (robustDecode candidate)
          allSingleChannelFailures
          survivesAllSingleChannelFailure = true →
        selectionCost resilientModel (robustDecode robustSelected) ≤
          selectionCost resilientModel (robustDecode candidate) := by
  decide

theorem robustSelected_is_minimum_cost_single_channel_resilient
    (candidate : RobustCandidate)
    (candidateRobust :
      FailureRobustBoundedVerifiesOn
        resilientModel
        (robustDecode candidate)
        allSingleChannelFailures
        survivesAllSingleChannelFailure) :
    selectionCost resilientModel (robustDecode robustSelected) ≤
      selectionCost resilientModel (robustDecode candidate) :=
  singleChannelCheckerCostMinimal candidate
    (robustBoundedVerifiesBool_complete
      resilientModel
      (robustDecode candidate)
      allSingleChannelFailures
      survivesAllSingleChannelFailure
      candidateRobust)

def singleChannelRobustCertificate :
    RobustEvidenceDebtCertificate
      resilientModel RobustCandidate robustDecode
      allSingleChannelFailures survivesAllSingleChannelFailure :=
  {
    selected := robustSelected
    selectedRobust :=
      robustSelected_verifies_all_single_channel_failures_on_list
    minimal :=
      robustSelected_is_minimum_cost_single_channel_resilient
  }

/-- No outage plus every independent trust-domain outage. -/
def allSingleDomainFailures : List (Option TrustDomain) :=
  [none,
    some .declarationPrimary,
    some .declarationBackup,
    some .targetedExecution,
    some .fullExecutionAudit,
    some .controlPrimary,
    some .controlBackup,
    some .publication]

theorem allSingleDomainFailures_complete
    (failure : Option TrustDomain) :
    failure ∈ allSingleDomainFailures := by
  cases failure with
  | none => simp [allSingleDomainFailures]
  | some failedDomain =>
      cases failedDomain <;> simp [allSingleDomainFailures]

theorem robustSelected_verifies_all_single_domain_failures_on_list :
    FailureRobustBoundedVerifiesOn
      resilientModel
      (robustDecode robustSelected)
      allSingleDomainFailures
      (survivesDomainFailure independentDomain) := by
  apply robustBoundedVerifiesBool_sound
  decide

theorem robustSelected_survives_any_single_domain_failure :
    FailureRobustBoundedVerifies
      resilientModel
      (robustDecode robustSelected)
      (survivesDomainFailure independentDomain) :=
  failure_list_complete_implies_full_robustness
    resilientModel
    (robustDecode robustSelected)
    allSingleDomainFailures
    (survivesDomainFailure independentDomain)
    allSingleDomainFailures_complete
    robustSelected_verifies_all_single_domain_failures_on_list

/-- Kernel computation independently checks the same 512 candidates against
    all eight independent-domain scenarios. -/
theorem singleDomainCheckerCostMinimal :
    ∀ candidate : RobustCandidate,
      robustBoundedVerifiesBool
          resilientModel
          (robustDecode candidate)
          allSingleDomainFailures
          (survivesDomainFailure independentDomain) = true →
        selectionCost resilientModel (robustDecode robustSelected) ≤
          selectionCost resilientModel (robustDecode candidate) := by
  decide

theorem robustSelected_is_minimum_cost_single_domain_resilient
    (candidate : RobustCandidate)
    (candidateRobust :
      FailureRobustBoundedVerifiesOn
        resilientModel
        (robustDecode candidate)
        allSingleDomainFailures
        (survivesDomainFailure independentDomain)) :
    selectionCost resilientModel (robustDecode robustSelected) ≤
      selectionCost resilientModel (robustDecode candidate) :=
  singleDomainCheckerCostMinimal candidate
    (robustBoundedVerifiesBool_complete
      resilientModel
      (robustDecode candidate)
      allSingleDomainFailures
      (survivesDomainFailure independentDomain)
      candidateRobust)

def singleDomainRobustCertificate :
    RobustEvidenceDebtCertificate
      resilientModel RobustCandidate robustDecode
      allSingleDomainFailures
      (survivesDomainFailure independentDomain) :=
  {
    selected := robustSelected
    selectedRobust :=
      robustSelected_verifies_all_single_domain_failures_on_list
    minimal :=
      robustSelected_is_minimum_cost_single_domain_resilient
  }

/-- Exact verification without failure tolerance costs 8 in the base model. -/
theorem exactVerificationCost :
    selectionCost model (decode selected) = 8 := by
  decide

/-- One-channel or one-domain resilience has exact minimum cost 20. -/
theorem exactRobustVerificationCost :
    singleChannelRobustCertificate.cost = 20 ∧
      singleDomainRobustCertificate.cost = 20 := by
  decide

/-- The exact resilience premium in this declared model is twelve cost units. -/
theorem singleFailureResiliencePremium :
    singleChannelRobustCertificate.cost =
      selectionCost model (decode selected) + 12 := by
  decide

end LeanFinance.Generated.ObservedCostModelTampering.RobustSynthesis
