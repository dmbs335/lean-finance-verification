import LeanFinance.Backtest.PointInTimeData

namespace LeanFinance.Backtest

/-- Two observations selected from one ALFRED/FRED real-time vintage. Calendar
    days and exact release instants are explicit because ALFRED's real-time date
    alone cannot establish intraday availability. -/
structure RevisionSignalSnapshot where
  vintageDay : Timestamp
  priorObservationDay : Timestamp
  currentObservationDay : Timestamp
  priorReleaseDay : Timestamp
  currentReleaseDay : Timestamp
  priorReleaseAt : Timestamp
  currentReleaseAt : Timestamp
  priorValueScaled : Int
  currentValueScaled : Int
  deriving Repr, DecidableEq

namespace RevisionSignalSnapshot

def signalScaled (snapshot : RevisionSignalSnapshot) : Int :=
  snapshot.currentValueScaled - snapshot.priorValueScaled

/-- Date-granular ALFRED availability: the vintage and both observation dates
    are no later than the decision's as-of day. -/
def AvailableAtVintageDay
    (snapshot : RevisionSignalSnapshot)
    (asOfDay : Timestamp) : Prop :=
  snapshot.vintageDay ≤ asOfDay ∧
    snapshot.priorObservationDay < snapshot.currentObservationDay ∧
      snapshot.currentObservationDay < asOfDay

/-- Strict availability at the actual decision instant. -/
def AvailableAtReleaseTime
    (snapshot : RevisionSignalSnapshot)
    (decisionAt : Timestamp) : Prop :=
  snapshot.priorReleaseAt ≤ decisionAt ∧
    snapshot.currentReleaseAt ≤ decisionAt

/-- A transformation can pass date-granular vintage checks while consuming an
    input released later than the decision instant. -/
def VintageValidButReleaseTimeLeaking
    (snapshot : RevisionSignalSnapshot)
    (asOfDay decisionAt : Timestamp) : Prop :=
  snapshot.AvailableAtVintageDay asOfDay ∧
    ¬ snapshot.AvailableAtReleaseTime decisionAt

/-- The nonleaking case: the selected transformation passes both policies. -/
def AvailableUnderBothPolicies
    (snapshot : RevisionSignalSnapshot)
    (asOfDay decisionAt : Timestamp) : Prop :=
  snapshot.AvailableAtVintageDay asOfDay ∧
    snapshot.AvailableAtReleaseTime decisionAt

/-- Exact same-day boundary where one selected input is released after the
    decision despite sharing the decision's calendar day. -/
def HasSameDayPostDecisionInput
    (snapshot : RevisionSignalSnapshot)
    (asOfDay decisionAt : Timestamp) : Prop :=
  (snapshot.priorReleaseDay = asOfDay ∧
      decisionAt < snapshot.priorReleaseAt) ∨
    (snapshot.currentReleaseDay = asOfDay ∧
      decisionAt < snapshot.currentReleaseAt)

/-- Fixed sign rule used by the controlled leakage study. -/
def position
    (snapshot : RevisionSignalSnapshot)
    (thresholdScaled : Int) : Int :=
  if thresholdScaled ≤ snapshot.signalScaled then 1 else -1

end RevisionSignalSnapshot

/-- One decision compared across four paths:

    * a date-granular ALFRED vintage transformation;
    * a release-time-strict transformation from that same vintage;
    * later revised values on the strict observation dates;
    * a naive latest-vintage path that may also change observation availability. -/
structure RevisionLeakageDecision where
  asOfDay : Timestamp
  decisionAt : Timestamp
  realizedReturnBps : Int
  signalThresholdScaled : Int
  vintageDate : RevisionSignalSnapshot
  releaseTimeStrict : RevisionSignalSnapshot
  latestSameObservations : RevisionSignalSnapshot
  latestNaive : RevisionSignalSnapshot
  vintageDateAvailable : vintageDate.AvailableAtVintageDay asOfDay
  releaseTimeStrictAvailable :
    releaseTimeStrict.AvailableUnderBothPolicies asOfDay decisionAt
  sameObservationDates :
    latestSameObservations.priorObservationDay =
        releaseTimeStrict.priorObservationDay ∧
      latestSameObservations.currentObservationDay =
        releaseTimeStrict.currentObservationDay
  latestSamePostDecisionDay :
    asOfDay < latestSameObservations.vintageDay
  latestNaivePostDecisionDay : asOfDay < latestNaive.vintageDay
  latestNaiveObservationsPrecede :
    latestNaive.priorObservationDay < latestNaive.currentObservationDay ∧
      latestNaive.currentObservationDay < asOfDay
  vintageTurnoverCostBps : Nat
  releaseTimeStrictTurnoverCostBps : Nat
  revisionOnlyTurnoverCostBps : Nat
  latestNaiveTurnoverCostBps : Nat

namespace RevisionLeakageDecision

def vintageDatePosition (decision : RevisionLeakageDecision) : Int :=
  decision.vintageDate.position decision.signalThresholdScaled

def releaseTimeStrictPosition (decision : RevisionLeakageDecision) : Int :=
  decision.releaseTimeStrict.position decision.signalThresholdScaled

def revisionOnlyPosition (decision : RevisionLeakageDecision) : Int :=
  decision.latestSameObservations.position decision.signalThresholdScaled

def latestNaivePosition (decision : RevisionLeakageDecision) : Int :=
  decision.latestNaive.position decision.signalThresholdScaled

def pathReturnBps
    (position realizedReturnBps : Int)
    (turnoverCostBps : Nat) : Int :=
  position * realizedReturnBps - Int.ofNat turnoverCostBps

def vintageDateReturnBps (decision : RevisionLeakageDecision) : Int :=
  pathReturnBps decision.vintageDatePosition decision.realizedReturnBps
    decision.vintageTurnoverCostBps

def releaseTimeStrictReturnBps
    (decision : RevisionLeakageDecision) : Int :=
  pathReturnBps decision.releaseTimeStrictPosition decision.realizedReturnBps
    decision.releaseTimeStrictTurnoverCostBps

def revisionOnlyReturnBps (decision : RevisionLeakageDecision) : Int :=
  pathReturnBps decision.revisionOnlyPosition decision.realizedReturnBps
    decision.revisionOnlyTurnoverCostBps

def latestNaiveReturnBps (decision : RevisionLeakageDecision) : Int :=
  pathReturnBps decision.latestNaivePosition decision.realizedReturnBps
    decision.latestNaiveTurnoverCostBps

def intradayReleaseLeakageBps
    (decision : RevisionLeakageDecision) : Int :=
  decision.vintageDateReturnBps - decision.releaseTimeStrictReturnBps

def revisionOnlyLeakageBps (decision : RevisionLeakageDecision) : Int :=
  decision.revisionOnlyReturnBps - decision.releaseTimeStrictReturnBps

def revisionPlusAvailabilityLeakageBps
    (decision : RevisionLeakageDecision) : Int :=
  decision.latestNaiveReturnBps - decision.releaseTimeStrictReturnBps

/-- A post-decision latest vintage cannot serve as the original decision's PIT
    input. -/
theorem latest_same_vintage_is_not_available_on_decision_day
    (decision : RevisionLeakageDecision) :
    ¬ decision.latestSameObservations.vintageDay ≤ decision.asOfDay := by
  intro available
  exact (Nat.not_lt_of_ge available) decision.latestSamePostDecisionDay

end RevisionLeakageDecision

def totalVintageDateReturnBps
    (decisions : List RevisionLeakageDecision) : Int :=
  decisions.foldl
    (fun total decision => total + decision.vintageDateReturnBps) 0

def totalReleaseTimeStrictReturnBps
    (decisions : List RevisionLeakageDecision) : Int :=
  decisions.foldl
    (fun total decision => total + decision.releaseTimeStrictReturnBps) 0

def totalRevisionOnlyReturnBps
    (decisions : List RevisionLeakageDecision) : Int :=
  decisions.foldl
    (fun total decision => total + decision.revisionOnlyReturnBps) 0

def totalLatestNaiveReturnBps
    (decisions : List RevisionLeakageDecision) : Int :=
  decisions.foldl
    (fun total decision => total + decision.latestNaiveReturnBps) 0

/-- Proof-carrying aggregate for date-only, release-time-strict, revision-only,
    and naive-latest paths. -/
structure RevisionLeakageStudyCertificate where
  studyId : String
  seriesId : String
  decisions : List RevisionLeakageDecision
  vintageDateTotalReturnBps : Int
  releaseTimeStrictTotalReturnBps : Int
  revisionOnlyTotalReturnBps : Int
  latestNaiveTotalReturnBps : Int
  intradayReleaseLeakageBps : Int
  revisionOnlyLeakageBps : Int
  revisionPlusAvailabilityLeakageBps : Int
  vintageDateTotalCorrect :
    vintageDateTotalReturnBps = totalVintageDateReturnBps decisions
  releaseTimeStrictTotalCorrect :
    releaseTimeStrictTotalReturnBps =
      totalReleaseTimeStrictReturnBps decisions
  revisionOnlyTotalCorrect :
    revisionOnlyTotalReturnBps = totalRevisionOnlyReturnBps decisions
  latestNaiveTotalCorrect :
    latestNaiveTotalReturnBps = totalLatestNaiveReturnBps decisions
  intradayLeakageCorrect :
    intradayReleaseLeakageBps =
      vintageDateTotalReturnBps - releaseTimeStrictTotalReturnBps
  revisionLeakageCorrect :
    revisionOnlyLeakageBps =
      revisionOnlyTotalReturnBps - releaseTimeStrictTotalReturnBps
  revisionPlusAvailabilityLeakageCorrect :
    revisionPlusAvailabilityLeakageBps =
      latestNaiveTotalReturnBps - releaseTimeStrictTotalReturnBps

namespace RevisionLeakageStudyCertificate

/-- Every selected strict-path transformation carries both date and exact
    release-time availability proofs. -/
def StrictPointInTime
    (certificate : RevisionLeakageStudyCertificate) : Prop :=
  ∀ decision,
    decision ∈ certificate.decisions →
      decision.releaseTimeStrict.AvailableUnderBothPolicies
        decision.asOfDay decision.decisionAt

theorem strict_path_is_point_in_time
    (certificate : RevisionLeakageStudyCertificate) :
    certificate.StrictPointInTime := by
  intro decision _member
  exact decision.releaseTimeStrictAvailable

theorem intraday_leakage_is_path_difference
    (certificate : RevisionLeakageStudyCertificate) :
    certificate.intradayReleaseLeakageBps =
      certificate.vintageDateTotalReturnBps -
        certificate.releaseTimeStrictTotalReturnBps :=
  certificate.intradayLeakageCorrect

theorem revision_leakage_is_path_difference
    (certificate : RevisionLeakageStudyCertificate) :
    certificate.revisionOnlyLeakageBps =
      certificate.revisionOnlyTotalReturnBps -
        certificate.releaseTimeStrictTotalReturnBps :=
  certificate.revisionLeakageCorrect

end RevisionLeakageStudyCertificate

end LeanFinance.Backtest
