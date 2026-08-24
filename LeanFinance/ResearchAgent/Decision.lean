namespace LeanFinance.ResearchAgent

/-- The machine gate can prepare a candidate for human review, request an
    evidence repair, or reject it. Autonomous deployment is intentionally absent
    from the state space. -/
inductive CandidateDecision where
  | advanceToHumanReview
  | repairEvidence
  | rejectCandidate
  deriving Repr, DecidableEq

/-- Normalized candidate state after alpha cleaning, uncertainty bounding,
    evidence-separation analysis, and deployability adjustments. -/
structure CandidateGate where
  integrityVerified : Bool
  repairPossible : Bool
  deployableLowerBoundBps : Int
  deriving Repr, DecidableEq

/-- Fail-closed policy: only integrity-verified candidates with a positive
    deployable lower bound reach mandatory human review. -/
def candidateDecision (candidate : CandidateGate) : CandidateDecision :=
  if candidate.integrityVerified then
    if 0 < candidate.deployableLowerBoundBps then
      .advanceToHumanReview
    else
      .rejectCandidate
  else if candidate.repairPossible then
    .repairEvidence
  else
    .rejectCandidate

/-- Machine advancement requires process integrity. -/
theorem advance_requires_integrity
    (candidate : CandidateGate)
    (advanced :
      candidateDecision candidate = .advanceToHumanReview) :
    candidate.integrityVerified = true := by
  cases integrity : candidate.integrityVerified with
  | false =>
      cases repairable : candidate.repairPossible <;>
        simp [candidateDecision, integrity, repairable] at advanced
  | true =>
      rfl

/-- Machine advancement also requires a positive deployable lower bound. -/
theorem advance_requires_positive_deployable_lower_bound
    (candidate : CandidateGate)
    (advanced :
      candidateDecision candidate = .advanceToHumanReview) :
    0 < candidate.deployableLowerBoundBps := by
  cases integrity : candidate.integrityVerified with
  | false =>
      cases repairable : candidate.repairPossible <;>
        simp [candidateDecision, integrity, repairable] at advanced
  | true =>
      by_cases positive : 0 < candidate.deployableLowerBoundBps
      · exact positive
      · simp [candidateDecision, integrity, positive] at advanced

/-- An unverified candidate with a representable repair receives an evidence
    obligation rather than review or silent acceptance. -/
theorem unverified_repairable_candidate_requests_repair
    (candidate : CandidateGate)
    (unverified : candidate.integrityVerified = false)
    (repairable : candidate.repairPossible = true) :
    candidateDecision candidate = .repairEvidence := by
  simp [candidateDecision, unverified, repairable]

/-- The strongest positive machine state is still only review preparation. -/
inductive ReviewState where
  | machinePrepared
  | humanApproved
  | humanRejected
  deriving Repr, DecidableEq

end LeanFinance.ResearchAgent
