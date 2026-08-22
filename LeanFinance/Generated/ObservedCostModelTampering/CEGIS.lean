import LeanFinance.Epistemic.CounterexampleGuided
import LeanFinance.Epistemic.FiniteSynthesisCompleteness
import LeanFinance.Generated.ObservedCostModelTampering.Search
import LeanFinance.Generated.ObservedCostModelTampering.Evidence

namespace LeanFinance.Generated.ObservedCostModelTampering.CEGIS

open LeanFinance.Epistemic
abbrev WorkflowAction := LeanFinance.Generated.ObservedCostModelTampering.Search.Action
abbrev EvidenceHistory := LeanFinance.Generated.ObservedCostModelTampering.Evidence.History
abbrev EvidenceChannel := LeanFinance.Generated.ObservedCostModelTampering.Evidence.Channel

def historyTrace : EvidenceHistory → List WorkflowAction
  | .undeclaredBaseline => [.executeBaseline, .publishResult, .anchorLedger]
  | .honest => [.declareBaseline, .executeBaseline, .publishResult, .anchorLedger]
  | .history2 => [.executeBaseline, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .history3 => [.executeBaseline, .readFutureData, .publishResult, .anchorLedger]
  | .history4 => [.executeBaseline, .tamperCostModel, .publishResult, .anchorLedger]
  | .hiddenSweep => [.declareBaseline, .executeBaseline, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .futureLeak => [.declareBaseline, .executeBaseline, .readFutureData, .publishResult, .anchorLedger]
  | .costModelTampering => [.declareBaseline, .executeBaseline, .tamperCostModel, .publishResult, .anchorLedger]
  | .history8 => [.executeBaseline, .executeHiddenSweep, .readFutureData, .publishResult, .anchorLedger]
  | .history9 => [.executeBaseline, .executeHiddenSweep, .tamperCostModel, .publishResult, .anchorLedger]
  | .history10 => [.executeBaseline, .readFutureData, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .history11 => [.executeBaseline, .readFutureData, .tamperCostModel, .publishResult, .anchorLedger]
  | .history12 => [.executeBaseline, .tamperCostModel, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .history13 => [.executeBaseline, .tamperCostModel, .readFutureData, .publishResult, .anchorLedger]
  | .dualAttack => [.declareBaseline, .executeBaseline, .executeHiddenSweep, .readFutureData, .publishResult, .anchorLedger]
  | .history15 => [.declareBaseline, .executeBaseline, .executeHiddenSweep, .tamperCostModel, .publishResult, .anchorLedger]
  | .history16 => [.declareBaseline, .executeBaseline, .readFutureData, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .history17 => [.declareBaseline, .executeBaseline, .readFutureData, .tamperCostModel, .publishResult, .anchorLedger]
  | .history18 => [.declareBaseline, .executeBaseline, .tamperCostModel, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .history19 => [.declareBaseline, .executeBaseline, .tamperCostModel, .readFutureData, .publishResult, .anchorLedger]
  | .history20 => [.executeBaseline, .executeHiddenSweep, .readFutureData, .tamperCostModel, .publishResult, .anchorLedger]
  | .history21 => [.executeBaseline, .executeHiddenSweep, .tamperCostModel, .readFutureData, .publishResult, .anchorLedger]
  | .history22 => [.executeBaseline, .readFutureData, .executeHiddenSweep, .tamperCostModel, .publishResult, .anchorLedger]
  | .history23 => [.executeBaseline, .readFutureData, .tamperCostModel, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .history24 => [.executeBaseline, .tamperCostModel, .executeHiddenSweep, .readFutureData, .publishResult, .anchorLedger]
  | .history25 => [.executeBaseline, .tamperCostModel, .readFutureData, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .history26 => [.declareBaseline, .executeBaseline, .executeHiddenSweep, .readFutureData, .tamperCostModel, .publishResult, .anchorLedger]
  | .history27 => [.declareBaseline, .executeBaseline, .executeHiddenSweep, .tamperCostModel, .readFutureData, .publishResult, .anchorLedger]
  | .history28 => [.declareBaseline, .executeBaseline, .readFutureData, .executeHiddenSweep, .tamperCostModel, .publishResult, .anchorLedger]
  | .history29 => [.declareBaseline, .executeBaseline, .readFutureData, .tamperCostModel, .executeHiddenSweep, .publishResult, .anchorLedger]
  | .history30 => [.declareBaseline, .executeBaseline, .tamperCostModel, .executeHiddenSweep, .readFutureData, .publishResult, .anchorLedger]
  | .history31 => [.declareBaseline, .executeBaseline, .tamperCostModel, .readFutureData, .executeHiddenSweep, .publishResult, .anchorLedger]

def toSensor : EvidenceChannel → LeanFinance.Generated.ObservedCostModelTampering.Search.Sensor
  | .selfReport => .selfReport
  | .resultBundle => .resultBundle
  | .rfc3161Anchor => .rfc3161Anchor
  | .fullExecutorLog => .fullExecutorLog
  | .targetedReceipt_executeHiddenSweep => .targetedReceipt_executeHiddenSweep
  | .targetedReceipt_readFutureData => .targetedReceipt_readFutureData
  | .targetedReceipt_tamperCostModel => .targetedReceipt_tamperCostModel

def rawObservation0 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.publishResult, .anchorLedger], state := [false, true, true] }

def rawObservation1 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.declareBaseline, .publishResult, .anchorLedger], state := [true, true, true] }

def rawObservation2 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.publishResult], state := [true] }

def rawObservation3 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.anchorLedger], state := [true] }

def rawObservation4 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.executeBaseline], state := [] }

def rawObservation5 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.executeBaseline, .executeHiddenSweep], state := [] }

def rawObservation6 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.executeBaseline, .readFutureData], state := [] }

def rawObservation7 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.executeBaseline, .executeHiddenSweep, .readFutureData], state := [] }

def rawObservation8 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.executeBaseline, .readFutureData, .executeHiddenSweep], state := [] }

def rawObservation9 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [], state := [] }

def rawObservation10 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.executeHiddenSweep], state := [] }

def rawObservation11 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.readFutureData], state := [] }

def rawObservation12 : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation :=
  { actions := [.tamperCostModel], state := [] }

def encodeObservation (value : LeanFinance.Generated.ObservedCostModelTampering.Search.RawObservation) :
    LeanFinance.Generated.ObservedCostModelTampering.Evidence.Observation :=
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
  else if value == rawObservation12 then .obs12
  else .obs0

def projectedObservation
    (channel : EvidenceChannel)
    (trace : List WorkflowAction) :
    LeanFinance.Generated.ObservedCostModelTampering.Evidence.Observation :=
  encodeObservation
    (LeanFinance.Generated.ObservedCostModelTampering.Search.projectTrace (toSensor channel) trace)

theorem generated_history_catalog_complete :
    LeanFinance.Generated.ObservedCostModelTampering.Evidence.histories.map historyTrace =
      LeanFinance.Generated.ObservedCostModelTampering.Search.generatedTraces := by
  decide

theorem generated_claim_matches_workflow :
    ∀ history : EvidenceHistory,
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.claim history =
        LeanFinance.Generated.ObservedCostModelTampering.Search.traceClaim (historyTrace history) := by
  intro history
  cases history <;> decide

theorem generated_observation_matches_workflow :
    ∀ channel : EvidenceChannel,
      ∀ history : EvidenceHistory,
        LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe channel history =
          projectedObservation channel (historyTrace history) := by
  intro channel history
  cases channel <;> cases history <;> decide

def initialSelection : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor]

def round0Before : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor]

def round0After : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor, .targetedReceipt_tamperCostModel]

def round0Counterexample :
    BoundedCounterexample LeanFinance.Generated.ObservedCostModelTampering.Evidence.model round0Before :=
  {
    left := .honest
    right := .costModelTampering
    leftMember := by simp [LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.histories]
    rightMember := by simp [LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.histories]
    claimDifferent := by simp [LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.claim]
    selectedAgree := by
      intro evidenceChannel member
      cases evidenceChannel <;>
        simp [round0Before, LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe] at member ⊢
  }

def refinementRound0 : CEGISRefinementRound LeanFinance.Generated.ObservedCostModelTampering.Evidence.model :=
  {
    before := round0Before
    after := round0After
    counterexample := round0Counterexample
    resolved := by
      refine ⟨.targetedReceipt_tamperCostModel, ?_, ?_⟩
      · simp [round0After]
      · decide
  }

theorem round0_refutes_before :
    ¬ BoundedSelectionVerifies LeanFinance.Generated.ObservedCostModelTampering.Evidence.model round0Before :=
  refinementRound0.beforeDoesNotVerify

def round1Before : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor, .targetedReceipt_tamperCostModel]

def round1After : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor, .targetedReceipt_readFutureData, .targetedReceipt_tamperCostModel]

def round1Counterexample :
    BoundedCounterexample LeanFinance.Generated.ObservedCostModelTampering.Evidence.model round1Before :=
  {
    left := .honest
    right := .futureLeak
    leftMember := by simp [LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.histories]
    rightMember := by simp [LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.histories]
    claimDifferent := by simp [LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.claim]
    selectedAgree := by
      intro evidenceChannel member
      cases evidenceChannel <;>
        simp [round1Before, LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe] at member ⊢
  }

def refinementRound1 : CEGISRefinementRound LeanFinance.Generated.ObservedCostModelTampering.Evidence.model :=
  {
    before := round1Before
    after := round1After
    counterexample := round1Counterexample
    resolved := by
      refine ⟨.targetedReceipt_readFutureData, ?_, ?_⟩
      · simp [round1After]
      · decide
  }

theorem round1_refutes_before :
    ¬ BoundedSelectionVerifies LeanFinance.Generated.ObservedCostModelTampering.Evidence.model round1Before :=
  refinementRound1.beforeDoesNotVerify

def round2Before : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor, .targetedReceipt_readFutureData, .targetedReceipt_tamperCostModel]

def round2After : List EvidenceChannel :=
  [.selfReport, .resultBundle, .rfc3161Anchor, .targetedReceipt_executeHiddenSweep, .targetedReceipt_readFutureData, .targetedReceipt_tamperCostModel]

def round2Counterexample :
    BoundedCounterexample LeanFinance.Generated.ObservedCostModelTampering.Evidence.model round2Before :=
  {
    left := .honest
    right := .hiddenSweep
    leftMember := by simp [LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.histories]
    rightMember := by simp [LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.histories]
    claimDifferent := by simp [LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.claim]
    selectedAgree := by
      intro evidenceChannel member
      cases evidenceChannel <;>
        simp [round2Before, LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.observe] at member ⊢
  }

def refinementRound2 : CEGISRefinementRound LeanFinance.Generated.ObservedCostModelTampering.Evidence.model :=
  {
    before := round2Before
    after := round2After
    counterexample := round2Counterexample
    resolved := by
      refine ⟨.targetedReceipt_executeHiddenSweep, ?_, ?_⟩
      · simp [round2After]
      · decide
  }

theorem round2_refutes_before :
    ¬ BoundedSelectionVerifies LeanFinance.Generated.ObservedCostModelTampering.Evidence.model round2Before :=
  refinementRound2.beforeDoesNotVerify

def cegisRounds :
    List (CEGISRefinementRound LeanFinance.Generated.ObservedCostModelTampering.Evidence.model) :=
  [refinementRound0, refinementRound1, refinementRound2]

abbrev RepairCandidate := Fin 16

/-- Repair candidates retain every already-deployed channel and select
    additional channels by bitmask. -/
def decodeRepairMask (mask : Nat) : List EvidenceChannel :=
  initialSelection
    ++ (if LeanFinance.Generated.ObservedCostModelTampering.Evidence.bitSelected mask 0 then [.fullExecutorLog] else [])
    ++ (if LeanFinance.Generated.ObservedCostModelTampering.Evidence.bitSelected mask 1 then [.targetedReceipt_executeHiddenSweep] else [])
    ++ (if LeanFinance.Generated.ObservedCostModelTampering.Evidence.bitSelected mask 2 then [.targetedReceipt_readFutureData] else [])
    ++ (if LeanFinance.Generated.ObservedCostModelTampering.Evidence.bitSelected mask 3 then [.targetedReceipt_tamperCostModel] else [])

def decodeRepair (candidate : RepairCandidate) : List EvidenceChannel :=
  decodeRepairMask candidate.val

def selectedRepair : RepairCandidate :=
  ⟨14, by decide⟩

def refinedSelection : List EvidenceChannel :=
  decodeRepair selectedRepair

theorem selected_repair_verifies :
    BoundedSelectionVerifies LeanFinance.Generated.ObservedCostModelTampering.Evidence.model refinedSelection := by
  apply boundedVerifiesBool_sound
  decide

/-- Kernel computation checks every repair that preserves the deployed
    baseline, establishing minimum total cost within that repair language. -/
theorem selected_repair_cost_minimal :
    ∀ candidate : RepairCandidate,
      boundedVerifiesBool LeanFinance.Generated.ObservedCostModelTampering.Evidence.model (decodeRepair candidate) = true →
        selectionCost LeanFinance.Generated.ObservedCostModelTampering.Evidence.model refinedSelection ≤
          selectionCost LeanFinance.Generated.ObservedCostModelTampering.Evidence.model (decodeRepair candidate) := by
  decide

theorem cegis_chain_connected :
    CEGISChain initialSelection cegisRounds refinedSelection := by
  simp [CEGISChain, cegisRounds, initialSelection, refinedSelection,
    round0Before, round0After, refinementRound0, round1Before, round1After, refinementRound1, round2Before, round2After, refinementRound2,
    selectedRepair, decodeRepair, decodeRepairMask, LeanFinance.Generated.ObservedCostModelTampering.Evidence.bitSelected]

def proofCarryingCEGIS :
    ProofCarryingCEGIS LeanFinance.Generated.ObservedCostModelTampering.Evidence.model
      RepairCandidate decodeRepair selectedRepair :=
  {
    initial := initialSelection
    rounds := cegisRounds
    connected := cegis_chain_connected
    historyComplete := by
      intro history
      cases history <;> simp [LeanFinance.Generated.ObservedCostModelTampering.Evidence.model, LeanFinance.Generated.ObservedCostModelTampering.Evidence.histories]
    finalVerified := selected_repair_verifies
    finalOptimal := by
      intro candidate candidateVerifies
      exact selected_repair_cost_minimal candidate
        (boundedVerifiesBool_complete LeanFinance.Generated.ObservedCostModelTampering.Evidence.model
          (decodeRepair candidate) candidateVerifies)
  }

theorem refined_selection_semantically_verifies :
    ChannelSelectionVerifies
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.model.observe
      (fun evidenceChannel => evidenceChannel ∈ refinedSelection)
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.model.ClaimHolds :=
  proofCarryingCEGIS.finalSemanticallyVerifies

theorem refined_selection_is_minimum_cost_repair
    (candidate : RepairCandidate)
    (candidateVerifies :
      BoundedSelectionVerifies LeanFinance.Generated.ObservedCostModelTampering.Evidence.model
        (decodeRepair candidate)) :
    selectionCost LeanFinance.Generated.ObservedCostModelTampering.Evidence.model refinedSelection ≤
      selectionCost LeanFinance.Generated.ObservedCostModelTampering.Evidence.model
        (decodeRepair candidate) :=
  proofCarryingCEGIS.finalCostMinimal
    candidate candidateVerifies

end LeanFinance.Generated.ObservedCostModelTampering.CEGIS
