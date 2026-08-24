import LeanFinance.Backtest.PointInTimeData

namespace LeanFinance.Backtest

/-- Two observations selected from one ALFRED/FRED real-time vintage. Values are
    exact scaled integers supplied by the external parser. -/
structure RevisionSignalSnapshot where
  vintageAt : Timestamp
  priorObservationAt : Timestamp
  currentObservationAt : Timestamp
  priorValueScaled : Int
  currentValueScaled : Int
  deriving Repr, DecidableEq

namespace RevisionSignalSnapshot

def signalScaled (snapshot : RevisionSignalSnapshot) : Int :=
  snapshot.currentValueScaled - snapshot.priorValueScaled

/-- A snapshot is usable by a decision when its real-time vintage was available
    and both selected observation dates strictly precede the decision. -/
def AvailableAt
    (snapshot : RevisionSignalSnapshot)
    (decisionAt : Timestamp) : Prop :=
  snapshot.vintageAt ≤ decisionAt ∧
    snapshot.priorObservationAt < snapshot.currentObservationAt ∧
      snapshot.currentObservationAt < decisionAt

/-- Fixed sign rule used by the controlled revision-leakage study. -/
def position
    (snapshot : RevisionSignalSnapshot)
    (thresholdScaled : Int) : Int :=
  if thresholdScaled ≤ snapshot.signalScaled then 1 else -1

end RevisionSignalSnapshot

/-- One decision compared across three data paths:

    * the real-time vintage available at the decision;
    * later revised values on the same observation dates;
    * a naive latest-vintage path that may also change which observations appear
      available by the decision date. -/
structure RevisionLeakageDecision where
  decisionAt : Timestamp
  realizedReturnBps : Int
  signalThresholdScaled : Int
  realtime : RevisionSignalSnapshot
  latestSameObservations : RevisionSignalSnapshot
  latestNaive : RevisionSignalSnapshot
  realtimeAvailable : realtime.AvailableAt decisionAt
  sameObservationDates :
    latestSameObservations.priorObservationAt =
        realtime.priorObservationAt ∧
      latestSameObservations.currentObservationAt =
        realtime.currentObservationAt
  latestSamePostDecision :
    decisionAt < latestSameObservations.vintageAt
  latestNaivePostDecision : decisionAt < latestNaive.vintageAt
  latestNaiveObservationsPrecede :
    latestNaive.priorObservationAt < latestNaive.currentObservationAt ∧
      latestNaive.currentObservationAt < decisionAt
  realtimeTurnoverCostBps : Nat
  revisionOnlyTurnoverCostBps : Nat
  latestNaiveTurnoverCostBps : Nat

namespace RevisionLeakageDecision

def realtimePosition (decision : RevisionLeakageDecision) : Int :=
  decision.realtime.position decision.signalThresholdScaled

def revisionOnlyPosition (decision : RevisionLeakageDecision) : Int :=
  decision.latestSameObservations.position decision.signalThresholdScaled

def latestNaivePosition (decision : RevisionLeakageDecision) : Int :=
  decision.latestNaive.position decision.signalThresholdScaled

def pathReturnBps
    (position realizedReturnBps : Int)
    (turnoverCostBps : Nat) : Int :=
  position * realizedReturnBps - Int.ofNat turnoverCostBps

def realtimeReturnBps (decision : RevisionLeakageDecision) : Int :=
  pathReturnBps decision.realtimePosition decision.realizedReturnBps
    decision.realtimeTurnoverCostBps

def revisionOnlyReturnBps (decision : RevisionLeakageDecision) : Int :=
  pathReturnBps decision.revisionOnlyPosition decision.realizedReturnBps
    decision.revisionOnlyTurnoverCostBps

def latestNaiveReturnBps (decision : RevisionLeakageDecision) : Int :=
  pathReturnBps decision.latestNaivePosition decision.realizedReturnBps
    decision.latestNaiveTurnoverCostBps

def revisionOnlyLeakageBps (decision : RevisionLeakageDecision) : Int :=
  decision.revisionOnlyReturnBps - decision.realtimeReturnBps

def revisionPlusAvailabilityLeakageBps
    (decision : RevisionLeakageDecision) : Int :=
  decision.latestNaiveReturnBps - decision.realtimeReturnBps

/-- A post-decision latest vintage cannot serve as the strict PIT input for the
    original decision. -/
theorem latest_same_vintage_is_not_available_at_decision
    (decision : RevisionLeakageDecision) :
    ¬ decision.latestSameObservations.vintageAt ≤ decision.decisionAt := by
  intro available
  exact (Nat.not_lt_of_ge available) decision.latestSamePostDecision

end RevisionLeakageDecision

def totalRealtimeReturnBps
    (decisions : List RevisionLeakageDecision) : Int :=
  decisions.foldl
    (fun total decision => total + decision.realtimeReturnBps) 0

def totalRevisionOnlyReturnBps
    (decisions : List RevisionLeakageDecision) : Int :=
  decisions.foldl
    (fun total decision => total + decision.revisionOnlyReturnBps) 0

def totalLatestNaiveReturnBps
    (decisions : List RevisionLeakageDecision) : Int :=
  decisions.foldl
    (fun total decision => total + decision.latestNaiveReturnBps) 0

/-- Proof-carrying aggregate for a strict real-time path and two explicit
    post-decision counterfactuals. -/
structure RevisionLeakageStudyCertificate where
  studyId : String
  seriesId : String
  decisions : List RevisionLeakageDecision
  realtimeTotalReturnBps : Int
  revisionOnlyTotalReturnBps : Int
  latestNaiveTotalReturnBps : Int
  revisionOnlyLeakageBps : Int
  revisionPlusAvailabilityLeakageBps : Int
  realtimeTotalCorrect :
    realtimeTotalReturnBps = totalRealtimeReturnBps decisions
  revisionOnlyTotalCorrect :
    revisionOnlyTotalReturnBps = totalRevisionOnlyReturnBps decisions
  latestNaiveTotalCorrect :
    latestNaiveTotalReturnBps = totalLatestNaiveReturnBps decisions
  revisionLeakageCorrect :
    revisionOnlyLeakageBps =
      revisionOnlyTotalReturnBps - realtimeTotalReturnBps
  revisionPlusAvailabilityLeakageCorrect :
    revisionPlusAvailabilityLeakageBps =
      latestNaiveTotalReturnBps - realtimeTotalReturnBps

namespace RevisionLeakageStudyCertificate

/-- Every decision in the strict path carries its own availability proof. -/
def StrictPointInTime
    (certificate : RevisionLeakageStudyCertificate) : Prop :=
  ∀ decision,
    decision ∈ certificate.decisions →
      decision.realtime.AvailableAt decision.decisionAt

theorem strict_path_is_point_in_time
    (certificate : RevisionLeakageStudyCertificate) :
    certificate.StrictPointInTime := by
  intro decision _member
  exact decision.realtimeAvailable

theorem revision_leakage_is_path_difference
    (certificate : RevisionLeakageStudyCertificate) :
    certificate.revisionOnlyLeakageBps =
      certificate.revisionOnlyTotalReturnBps -
        certificate.realtimeTotalReturnBps :=
  certificate.revisionLeakageCorrect

theorem naive_latest_leakage_is_path_difference
    (certificate : RevisionLeakageStudyCertificate) :
    certificate.revisionPlusAvailabilityLeakageBps =
      certificate.latestNaiveTotalReturnBps -
        certificate.realtimeTotalReturnBps :=
  certificate.revisionPlusAvailabilityLeakageCorrect

end RevisionLeakageStudyCertificate

end LeanFinance.Backtest
