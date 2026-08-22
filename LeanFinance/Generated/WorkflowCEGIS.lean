import LeanFinance.Epistemic.CounterexampleGuided
import LeanFinance.Epistemic.FiniteSynthesisCompleteness
import LeanFinance.Generated.WorkflowIntegrity.Search
import LeanFinance.Generated.WorkflowIntegrity.Evidence

namespace LeanFinance.Generated.WorkflowIntegrity.CEGIS

open LeanFinance.Epistemic
abbrev WorkflowAction := LeanFinance.Generated.WorkflowIntegrity.Search.Action
abbrev EvidenceHistory := LeanFinance.Generated.WorkflowIntegrity.Evidence.History
abbrev EvidenceChannel := LeanFinance.Generated.WorkflowIntegrity.Evidence.Channel

def historyTrace : EvidenceHistory → List WorkflowAction
  | .undeclaredBaseline => [.executeBaseline, .publishResult, .anchorLedger]
  | .honest => [.declareBaseline, .executeBaseline, .publishResult, .anchorLedger]
  | .history2 => [.executeBaseline, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .history3 => [.executeBaseline, .readFutureData, .publishResult, .anchorLedger]
  | .hiddenSweep => [.declareBaseline, .executeBaseline, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .futureLeak => [.declareBaseline, .executeBaseline, .readFutureData, .publishResult, .anchorLedger]
  | .history6 => [.executeBaseline, .executeHiddenSweep, .readFutureData, .publishResult, .anchorLedger]
  | .history7 => [.executeBaseline, .readFutureData, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .dualAttack => [.declareBaseline, .executeBaseline, .executeHiddenSweep, .readFutureData, .publishResult, .anchorLedger]
  | .history9 => [.declareBaseline, .executeBaseline, .readFutureData, .executeHiddenSweep, .publishResult, .anchorLedger]

def toSensor : EvidenceChannel → LeanFinance.Generated.WorkflowIntegrity.Search.Sensor
  | .selfReport => .selfReport
  | .resultBundle => .resultBundle
  | .rfc3161Anchor => .rfc3161Anchor
  | .fullExecutorLog => .fullExecutorLog
  | .targetedReceipt_executeHiddenSweep => .targetedReceipt_executeHiddenSweep
  | .targetedReceipt_readFutureData => .targetedReceipt_readFutureData

def rawObservation0 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.publishResult, .anchorLedger], state := [false, true, true] }

def rawObservation1 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.declareBaseline, .publishResult, .anchorLedger], state := [true, true, true] }

def rawObservation2 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.publishResult], state := [true] }

def rawObservation3 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.anchorLedger], state := [true] }

def rawObservation4 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.executeBaseline], state := [] }

def rawObservation5 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.executeBaseline, .executeHiddenSweep], state := [] }

def rawObservation6 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.executeBaseline, .readFutureData], state := [] }

def rawObservation7 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.executeBaseline, .executeHiddenSweep, .readFutureData], state := [] }

def rawObservation8 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.executeBaseline, .readFutureData, .executeHiddenSweep], state := [] }

def rawObservation9 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [], state := [] }

def rawObservation10 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.executeHiddenSweep], state := [] }

def rawObservation11 : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation :=
  { actions := [.readFutureData], state := [] }

def encodeObservation (value : LeanFinance.Generated.WorkflowIntegrity.Search.RawObservation) :
    LeanFinance.Generated.WorkflowIntegrity.Evidence.Observation :=
  if value == rawObservation0 then .obs0
  else if value == rawObservation1 then .obs1
  else if value == rawObservation2 then .obs2
  else if value == rawObservation3 then .obs3
  else if value == rawObservation4 then .obs4
  else if value == rawObservation5 then .obs5
  else if value == rawObservation6 then .obs6
  else if value == rawObservation7 then .obs7
  else if value == rawObservation8 then .obs8
  else if value == rawObservation9 then .obs9
  else if value == rawObservation10 then .obs10
  else if value == rawObservation11 then .obs11
  else .obs0

def projectedObservation
    (channel : EvidenceChannel)
    (trace : List WorkflowAction) :
    LeanFinance.Generated.WorkflowIntegrity.Evidence.Observation :=
  encodeObservation
    (LeanFinance.Generated.WorkflowIntegrity.Search.projectTrace (toSensor channel) trace)

theorem generated_history_catalog_complete :
    LeanFinance.Generated.WorkflowIntegrity.Evidence.histories.map historyTrace =
      LeanFinance.Generated.WorkflowIntegrity.Search.generatedTraces := by
  decide

theorem generated_claim_matches_workflow :
    ∀ history : EvidenceHistory,
      LeanFinance.Generated.WorkflowIntegrity.Evidence.claim history =
        LeanFinance.Generated.WorkflowIntegrity.Search.traceClaim (historyTrace history) := by
  intro history
  cases history <;> decide

theorem generated_observation_matches_workflow :
    ∀ channel : EvidenceChannel,
      ∀ history : EvidenceHistory,
        LeanFinance.Generated.WorkflowIntegrity.Evidence.observe channel history =
          projectedObservation channel (historyTrace history) := by
  intro channel history
  cases channel <;> cases history <;> decide

def initialSelection : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor]

def round0Before : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor]

def round0After : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor, .targetedReceipt_readFutureData]

def round0Counterexample :
    BoundedCounterexample LeanFinance.Generated.WorkflowIntegrity.Evidence.model round0Before :=
  {
    left := .honest
    right := .futureLeak
    leftMember := by simp [LeanFinance.Generated.WorkflowIntegrity.Evidence.model, LeanFinance.Generated.WorkflowIntegrity.Evidence.histories]
    rightMember := by simp [LeanFinance.Generated.WorkflowIntegrity.Evidence.model, LeanFinance.Generated.WorkflowIntegrity.Evidence.histories]
    claimDifferent := by simp [LeanFinance.Generated.WorkflowIntegrity.Evidence.model, LeanFinance.Generated.WorkflowIntegrity.Evidence.claim]
    selectedAgree := by
      intro evidenceChannel member
      cases evidenceChannel <;>
        simp [round0Before, LeanFinance.Generated.WorkflowIntegrity.Evidence.model, LeanFinance.Generated.WorkflowIntegrity.Evidence.observe] at member ⊢
  }

def refinementRound0 : CEGISRefinementRound LeanFinance.Generated.WorkflowIntegrity.Evidence.model :=
  {
    before := round0Before
    after := round0After
    counterexample := round0Counterexample
    resolved := by
      refine ⟨.targetedReceipt_readFutureData, ?_, ?_⟩
      · simp [round0After]
      · decide
  }

theorem round0_refutes_before :
    ¬ BoundedSelectionVerifies LeanFinance.Generated.WorkflowIntegrity.Evidence.model round0Before :=
  refinementRound0.beforeDoesNotVerify

def round1Before : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor, .targetedReceipt_readFutureData]

def round1After : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor, .targetedReceipt_executeHiddenSweep, .targetedReceipt_readFutureData]

def round1Counterexample :
    BoundedCounterexample LeanFinance.Generated.WorkflowIntegrity.Evidence.model round1Before :=
  {
    left := .honest
    right := .hiddenSweep
    leftMember := by simp [LeanFinance.Generated.WorkflowIntegrity.Evidence.model, LeanFinance.Generated.WorkflowIntegrity.Evidence.histories]
    rightMember := by simp [LeanFinance.Generated.WorkflowIntegrity.Evidence.model, LeanFinance.Generated.WorkflowIntegrity.Evidence.histories]
    claimDifferent := by simp [LeanFinance.Generated.WorkflowIntegrity.Evidence.model, LeanFinance.Generated.WorkflowIntegrity.Evidence.claim]
    selectedAgree := by
      intro evidenceChannel member
      cases evidenceChannel <;>
        simp [round1Before, LeanFinance.Generated.WorkflowIntegrity.Evidence.model, LeanFinance.Generated.WorkflowIntegrity.Evidence.observe] at member ⊢
  }

def refinementRound1 : CEGISRefinementRound LeanFinance.Generated.WorkflowIntegrity.Evidence.model :=
  {
    before := round1Before
    after := round1After
    counterexample := round1Counterexample
    resolved := by
      refine ⟨.targetedReceipt_executeHiddenSweep, ?_, ?_⟩
      · simp [round1After]
      · decide
  }

theorem round1_refutes_before :
    ¬ BoundedSelectionVerifies LeanFinance.Generated.WorkflowIntegrity.Evidence.model round1Before :=
  refinementRound1.beforeDoesNotVerify

def cegisRounds :
    List (CEGISRefinementRound LeanFinance.Generated.WorkflowIntegrity.Evidence.model) :=
  [refinementRound0, refinementRound1]

abbrev RepairCandidate := Fin 8

/-- Repair candidates retain every already-deployed channel and select
    additional channels by bitmask. -/
def decodeRepairMask (mask : Nat) : List EvidenceChannel :=
  initialSelection
    ++ (if LeanFinance.Generated.WorkflowIntegrity.Evidence.bitSelected mask 0 then [.fullExecutorLog] else [])
    ++ (if LeanFinance.Generated.WorkflowIntegrity.Evidence.bitSelected mask 1 then [.targetedReceipt_executeHiddenSweep] else [])
    ++ (if LeanFinance.Generated.WorkflowIntegrity.Evidence.bitSelected mask 2 then [.targetedReceipt_readFutureData] else [])

def decodeRepair (candidate : RepairCandidate) : List EvidenceChannel :=
  decodeRepairMask candidate.val

def selectedRepair : RepairCandidate :=
  ⟨6, by decide⟩

def refinedSelection : List EvidenceChannel :=
  decodeRepair selectedRepair

theorem selected_repair_verifies :
    BoundedSelectionVerifies LeanFinance.Generated.WorkflowIntegrity.Evidence.model refinedSelection := by
  apply boundedVerifiesBool_sound
  decide

/-- Kernel computation checks every repair that preserves the deployed
    baseline, establishing minimum total cost within that repair language. -/
theorem selected_repair_cost_minimal :
    ∀ candidate : RepairCandidate,
      boundedVerifiesBool LeanFinance.Generated.WorkflowIntegrity.Evidence.model (decodeRepair candidate) = true →
        selectionCost LeanFinance.Generated.WorkflowIntegrity.Evidence.model refinedSelection ≤
          selectionCost LeanFinance.Generated.WorkflowIntegrity.Evidence.model (decodeRepair candidate) := by
  decide

theorem cegis_chain_connected :
    CEGISChain initialSelection cegisRounds refinedSelection := by
  simp [CEGISChain, cegisRounds, initialSelection, refinedSelection,
    round0Before, round0After, refinementRound0, round1Before, round1After, refinementRound1,
    selectedRepair, decodeRepair, decodeRepairMask, LeanFinance.Generated.WorkflowIntegrity.Evidence.bitSelected]

def proofCarryingCEGIS :
    ProofCarryingCEGIS LeanFinance.Generated.WorkflowIntegrity.Evidence.model
      RepairCandidate decodeRepair selectedRepair :=
  {
    initial := initialSelection
    rounds := cegisRounds
    connected := cegis_chain_connected
    historyComplete := by
      intro history
      cases history <;> simp [LeanFinance.Generated.WorkflowIntegrity.Evidence.model, LeanFinance.Generated.WorkflowIntegrity.Evidence.histories]
    finalVerified := selected_repair_verifies
    finalOptimal := by
      intro candidate candidateVerifies
      exact selected_repair_cost_minimal candidate
        (boundedVerifiesBool_complete LeanFinance.Generated.WorkflowIntegrity.Evidence.model
          (decodeRepair candidate) candidateVerifies)
  }

theorem refined_selection_semantically_verifies :
    ChannelSelectionVerifies
      LeanFinance.Generated.WorkflowIntegrity.Evidence.model.observe
      (fun evidenceChannel => evidenceChannel ∈ refinedSelection)
      LeanFinance.Generated.WorkflowIntegrity.Evidence.model.ClaimHolds :=
  proofCarryingCEGIS.finalSemanticallyVerifies

theorem refined_selection_is_minimum_cost_repair
    (candidate : RepairCandidate)
    (candidateVerifies :
      BoundedSelectionVerifies LeanFinance.Generated.WorkflowIntegrity.Evidence.model
        (decodeRepair candidate)) :
    selectionCost LeanFinance.Generated.WorkflowIntegrity.Evidence.model refinedSelection ≤
      selectionCost LeanFinance.Generated.WorkflowIntegrity.Evidence.model
        (decodeRepair candidate) :=
  proofCarryingCEGIS.finalCostMinimal
    candidate candidateVerifies

end LeanFinance.Generated.WorkflowIntegrity.CEGIS
