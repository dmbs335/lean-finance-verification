import LeanFinance.Backtest.ResearchAgent

namespace LeanFinance.Examples.ResearchAgent

open LeanFinance.Backtest

def certifiableCandidate : ResearchCandidateGate :=
  { integrityVerified := true
    repairPossible := true
    deployableLowerBoundBps := 20 }

def evidenceGapCandidate : ResearchCandidateGate :=
  { integrityVerified := false
    repairPossible := true
    deployableLowerBoundBps := 80 }

def overcrowdedCandidate : ResearchCandidateGate :=
  { integrityVerified := true
    repairPossible := true
    deployableLowerBoundBps := -5 }

theorem certifiable_candidate_advances_only_to_review :
    researchAgentDecision certifiableCandidate =
      .advanceToHumanReview := by
  decide

theorem evidence_gap_requests_repair_despite_high_observed_alpha :
    researchAgentDecision evidenceGapCandidate = .repairEvidence := by
  decide

theorem negative_deployable_lower_bound_is_rejected :
    researchAgentDecision overcrowdedCandidate = .rejectCandidate := by
  decide

end LeanFinance.Examples.ResearchAgent
