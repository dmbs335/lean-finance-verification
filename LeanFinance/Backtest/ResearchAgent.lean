namespace LeanFinance.Backtest

/-- The agent may prepare a candidate for human review, request evidence repair,
    or reject it. It never has an autonomous deployment state. -/
inductive ResearchAgentDecision where
  | advanceToHumanReview
  | repairEvidence
  | rejectCandidate
  deriving Repr, DecidableEq

/-- Minimal normalized gate after backtest, adversarial analysis, evidence
    synthesis, and deployability adjustments. -/
structure ResearchCandidateGate where
  integrityVerified : Bool
  repairPossible : Bool
  deployableLowerBoundBps : Int
  deriving Repr, DecidableEq

/-- Deterministic safety gate. Unverified research is repaired when possible and
    rejected otherwise. Verified research advances only when its deployable
    lower bound is positive. -/
def researchAgentDecision
    (candidate : ResearchCandidateGate) : ResearchAgentDecision :=
  if candidate.integrityVerified then
    if 0 < candidate.deployableLowerBoundBps then
      .advanceToHumanReview
    else
      .rejectCandidate
  else if candidate.repairPossible then
    .repairEvidence
  else
    .rejectCandidate

/-- Advancement requires verified process integrity. -/
theorem advance_requires_integrity
    (candidate : ResearchCandidateGate)
    (advanced :
      researchAgentDecision candidate = .advanceToHumanReview) :
    candidate.integrityVerified = true := by
  cases integrity : candidate.integrityVerified <;>
    simp [researchAgentDecision, integrity] at advanced ⊢

/-- Advancement also requires a positive deployable lower bound after modeled
    impact and capacity adjustments. -/
theorem advance_requires_positive_deployable_lower_bound
    (candidate : ResearchCandidateGate)
    (advanced :
      researchAgentDecision candidate = .advanceToHumanReview) :
    0 < candidate.deployableLowerBoundBps := by
  cases integrity : candidate.integrityVerified with
  | false =>
      simp [researchAgentDecision, integrity] at advanced
  | true =>
      by_cases positive : 0 < candidate.deployableLowerBoundBps
      · exact positive
      · simp [researchAgentDecision, integrity, positive] at advanced

/-- Unverified candidates with a feasible evidence repair are never advanced or
    silently rejected; they receive a repair obligation. -/
theorem unverified_repairable_candidate_requests_repair
    (candidate : ResearchCandidateGate)
    (unverified : candidate.integrityVerified = false)
    (repairable : candidate.repairPossible = true) :
    researchAgentDecision candidate = .repairEvidence := by
  simp [researchAgentDecision, unverified, repairable]

/-- Human approval remains outside the agent's formal state machine. -/
inductive ResearchReviewState where
  | machinePrepared
  | humanApproved
  | humanRejected
  deriving Repr, DecidableEq

end LeanFinance.Backtest
