import LeanFinance.Backtest.RevisionLeakage

namespace LeanFinance.Examples.RevisionLeakage

open LeanFinance.Backtest

def decisionOne : RevisionLeakageDecision :=
  { decisionAt := 25
    realizedReturnBps := 30
    signalThresholdScaled := 0
    realtime :=
      { vintageAt := 25
        priorObservationAt := 10
        currentObservationAt := 20
        priorValueScaled := 100000
        currentValueScaled := 99000 }
    latestSameObservations :=
      { vintageAt := 60
        priorObservationAt := 10
        currentObservationAt := 20
        priorValueScaled := 100000
        currentValueScaled := 101000 }
    latestNaive :=
      { vintageAt := 60
        priorObservationAt := 20
        currentObservationAt := 30
        priorValueScaled := 101000
        currentValueScaled := 103000 }
    realtimeAvailable := by decide
    sameObservationDates := ⟨rfl, rfl⟩
    latestSamePostDecision := by decide
    latestNaivePostDecision := by decide
    latestNaiveObservationsPrecede := by decide
    realtimeTurnoverCostBps := 1
    revisionOnlyTurnoverCostBps := 1
    latestNaiveTurnoverCostBps := 1 }

def decisionTwo : RevisionLeakageDecision :=
  { decisionAt := 35
    realizedReturnBps := 40
    signalThresholdScaled := 0
    realtime :=
      { vintageAt := 35
        priorObservationAt := 20
        currentObservationAt := 30
        priorValueScaled := 99000
        currentValueScaled := 98000 }
    latestSameObservations :=
      { vintageAt := 60
        priorObservationAt := 20
        currentObservationAt := 30
        priorValueScaled := 101000
        currentValueScaled := 103000 }
    latestNaive :=
      { vintageAt := 60
        priorObservationAt := 30
        currentObservationAt := 40
        priorValueScaled := 103000
        currentValueScaled := 102000 }
    realtimeAvailable := by decide
    sameObservationDates := ⟨rfl, rfl⟩
    latestSamePostDecision := by decide
    latestNaivePostDecision := by decide
    latestNaiveObservationsPrecede := by decide
    realtimeTurnoverCostBps := 0
    revisionOnlyTurnoverCostBps := 0
    latestNaiveTurnoverCostBps := 1 }

def decisionThree : RevisionLeakageDecision :=
  { decisionAt := 45
    realizedReturnBps := -20
    signalThresholdScaled := 0
    realtime :=
      { vintageAt := 45
        priorObservationAt := 30
        currentObservationAt := 40
        priorValueScaled := 98000
        currentValueScaled := 100000 }
    latestSameObservations :=
      { vintageAt := 60
        priorObservationAt := 30
        currentObservationAt := 40
        priorValueScaled := 103000
        currentValueScaled := 102000 }
    latestNaive :=
      { vintageAt := 60
        priorObservationAt := 40
        currentObservationAt := 44
        priorValueScaled := 102000
        currentValueScaled := 105000 }
    realtimeAvailable := by decide
    sameObservationDates := ⟨rfl, rfl⟩
    latestSamePostDecision := by decide
    latestNaivePostDecision := by decide
    latestNaiveObservationsPrecede := by decide
    realtimeTurnoverCostBps := 1
    revisionOnlyTurnoverCostBps := 1
    latestNaiveTurnoverCostBps := 1 }

def decisionFour : RevisionLeakageDecision :=
  { decisionAt := 55
    realizedReturnBps := 10
    signalThresholdScaled := 0
    realtime :=
      { vintageAt := 55
        priorObservationAt := 30
        currentObservationAt := 40
        priorValueScaled := 98000
        currentValueScaled := 100000 }
    latestSameObservations :=
      { vintageAt := 60
        priorObservationAt := 30
        currentObservationAt := 40
        priorValueScaled := 103000
        currentValueScaled := 102000 }
    latestNaive :=
      { vintageAt := 60
        priorObservationAt := 40
        currentObservationAt := 50
        priorValueScaled := 102000
        currentValueScaled := 105000 }
    realtimeAvailable := by decide
    sameObservationDates := ⟨rfl, rfl⟩
    latestSamePostDecision := by decide
    latestNaivePostDecision := by decide
    latestNaiveObservationsPrecede := by decide
    realtimeTurnoverCostBps := 0
    revisionOnlyTurnoverCostBps := 0
    latestNaiveTurnoverCostBps := 0 }

def decisions : List RevisionLeakageDecision :=
  [decisionOne, decisionTwo, decisionThree, decisionFour]

theorem controlled_realtime_total :
    totalRealtimeReturnBps decisions = -82 := by
  decide

theorem controlled_revision_only_total :
    totalRevisionOnlyReturnBps decisions = 78 := by
  decide

theorem controlled_latest_naive_total :
    totalLatestNaiveReturnBps decisions = -23 := by
  decide

def certificate : RevisionLeakageStudyCertificate :=
  { studyId := "synthetic-alfred-revision-leakage"
    seriesId := "TESTREV"
    decisions := decisions
    realtimeTotalReturnBps := -82
    revisionOnlyTotalReturnBps := 78
    latestNaiveTotalReturnBps := -23
    revisionOnlyLeakageBps := 160
    revisionPlusAvailabilityLeakageBps := 59
    realtimeTotalCorrect := by decide
    revisionOnlyTotalCorrect := by decide
    latestNaiveTotalCorrect := by decide
    revisionLeakageCorrect := by decide
    revisionPlusAvailabilityLeakageCorrect := by decide }

theorem strict_path_is_verified_point_in_time :
    certificate.StrictPointInTime :=
  certificate.strict_path_is_point_in_time

theorem pure_revision_counterfactual_adds_one_hundred_sixty_bps :
    certificate.revisionOnlyLeakageBps = 160 := by
  decide

theorem naive_latest_counterfactual_adds_fifty_nine_bps :
    certificate.revisionPlusAvailabilityLeakageBps = 59 := by
  decide

theorem latest_vintage_cannot_be_used_for_original_decision :
    ¬ decisionOne.latestSameObservations.vintageAt ≤
      decisionOne.decisionAt :=
  decisionOne.latest_same_vintage_is_not_available_at_decision

end LeanFinance.Examples.RevisionLeakage
