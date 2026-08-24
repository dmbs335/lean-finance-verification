import LeanFinance.Backtest.RevisionLeakage

namespace LeanFinance.Examples.RevisionLeakage

open LeanFinance.Backtest

def observationA : Timestamp := 10
def observationB : Timestamp := 20
def observationC : Timestamp := 29
def observationD : Timestamp := 39
def observationE : Timestamp := 49
def observationF : Timestamp := 59

def decisionOne : RevisionLeakageDecision :=
  { asOfDay := 30
    decisionAt := 3009
    realizedReturnBps := 30
    signalThresholdScaled := 0
    vintageDate :=
      { vintageDay := 30
        priorObservationDay := observationB
        currentObservationDay := observationC
        priorReleaseDay := 25
        currentReleaseDay := 30
        priorReleaseAt := 2514
        currentReleaseAt := 3014
        priorValueScaled := 100000
        currentValueScaled := 99000 }
    releaseTimeStrict :=
      { vintageDay := 30
        priorObservationDay := observationA
        currentObservationDay := observationB
        priorReleaseDay := 15
        currentReleaseDay := 25
        priorReleaseAt := 1514
        currentReleaseAt := 2514
        priorValueScaled := 99000
        currentValueScaled := 100000 }
    latestSameObservations :=
      { vintageDay := 80
        priorObservationDay := observationA
        currentObservationDay := observationB
        priorReleaseDay := 15
        currentReleaseDay := 25
        priorReleaseAt := 1514
        currentReleaseAt := 2514
        priorValueScaled := 99000
        currentValueScaled := 100000 }
    latestNaive :=
      { vintageDay := 80
        priorObservationDay := 25
        currentObservationDay := 28
        priorReleaseDay := 42
        currentReleaseDay := 43
        priorReleaseAt := 4214
        currentReleaseAt := 4314
        priorValueScaled := 10000
        currentValueScaled := 20000 }
    vintageDateAvailable := by decide
    releaseTimeStrictAvailable := by decide
    sameObservationDates := ⟨rfl, rfl⟩
    latestSamePostDecisionDay := by decide
    latestNaivePostDecisionDay := by decide
    latestNaiveObservationsPrecede := by decide
    vintageTurnoverCostBps := 1
    releaseTimeStrictTurnoverCostBps := 1
    revisionOnlyTurnoverCostBps := 1
    latestNaiveTurnoverCostBps := 1 }

def decisionTwo : RevisionLeakageDecision :=
  { asOfDay := 40
    decisionAt := 4015
    realizedReturnBps := 40
    signalThresholdScaled := 0
    vintageDate :=
      { vintageDay := 40
        priorObservationDay := observationC
        currentObservationDay := observationD
        priorReleaseDay := 30
        currentReleaseDay := 40
        priorReleaseAt := 3014
        currentReleaseAt := 4014
        priorValueScaled := 99000
        currentValueScaled := 98000 }
    releaseTimeStrict :=
      { vintageDay := 40
        priorObservationDay := observationC
        currentObservationDay := observationD
        priorReleaseDay := 30
        currentReleaseDay := 40
        priorReleaseAt := 3014
        currentReleaseAt := 4014
        priorValueScaled := 99000
        currentValueScaled := 98000 }
    latestSameObservations :=
      { vintageDay := 80
        priorObservationDay := observationC
        currentObservationDay := observationD
        priorReleaseDay := 30
        currentReleaseDay := 40
        priorReleaseAt := 3014
        currentReleaseAt := 4014
        priorValueScaled := 101000
        currentValueScaled := 103000 }
    latestNaive :=
      { vintageDay := 80
        priorObservationDay := 35
        currentObservationDay := 38
        priorReleaseDay := 52
        currentReleaseDay := 53
        priorReleaseAt := 5214
        currentReleaseAt := 5314
        priorValueScaled := 20000
        currentValueScaled := 10000 }
    vintageDateAvailable := by decide
    releaseTimeStrictAvailable := by decide
    sameObservationDates := ⟨rfl, rfl⟩
    latestSamePostDecisionDay := by decide
    latestNaivePostDecisionDay := by decide
    latestNaiveObservationsPrecede := by decide
    vintageTurnoverCostBps := 0
    releaseTimeStrictTurnoverCostBps := 1
    revisionOnlyTurnoverCostBps := 0
    latestNaiveTurnoverCostBps := 1 }

def decisionThree : RevisionLeakageDecision :=
  { asOfDay := 50
    decisionAt := 5015
    realizedReturnBps := -20
    signalThresholdScaled := 0
    vintageDate :=
      { vintageDay := 50
        priorObservationDay := observationD
        currentObservationDay := observationE
        priorReleaseDay := 40
        currentReleaseDay := 50
        priorReleaseAt := 4014
        currentReleaseAt := 5014
        priorValueScaled := 98000
        currentValueScaled := 100000 }
    releaseTimeStrict :=
      { vintageDay := 50
        priorObservationDay := observationD
        currentObservationDay := observationE
        priorReleaseDay := 40
        currentReleaseDay := 50
        priorReleaseAt := 4014
        currentReleaseAt := 5014
        priorValueScaled := 98000
        currentValueScaled := 100000 }
    latestSameObservations :=
      { vintageDay := 80
        priorObservationDay := observationD
        currentObservationDay := observationE
        priorReleaseDay := 40
        currentReleaseDay := 50
        priorReleaseAt := 4014
        currentReleaseAt := 5014
        priorValueScaled := 103000
        currentValueScaled := 102000 }
    latestNaive :=
      { vintageDay := 80
        priorObservationDay := 45
        currentObservationDay := 48
        priorReleaseDay := 62
        currentReleaseDay := 63
        priorReleaseAt := 6214
        currentReleaseAt := 6314
        priorValueScaled := 10000
        currentValueScaled := 20000 }
    vintageDateAvailable := by decide
    releaseTimeStrictAvailable := by decide
    sameObservationDates := ⟨rfl, rfl⟩
    latestSamePostDecisionDay := by decide
    latestNaivePostDecisionDay := by decide
    latestNaiveObservationsPrecede := by decide
    vintageTurnoverCostBps := 1
    releaseTimeStrictTurnoverCostBps := 1
    revisionOnlyTurnoverCostBps := 1
    latestNaiveTurnoverCostBps := 1 }

def decisionFour : RevisionLeakageDecision :=
  { asOfDay := 60
    decisionAt := 6015
    realizedReturnBps := 10
    signalThresholdScaled := 0
    vintageDate :=
      { vintageDay := 60
        priorObservationDay := observationE
        currentObservationDay := observationF
        priorReleaseDay := 50
        currentReleaseDay := 60
        priorReleaseAt := 5014
        currentReleaseAt := 6016
        priorValueScaled := 100000
        currentValueScaled := 99000 }
    releaseTimeStrict :=
      { vintageDay := 60
        priorObservationDay := observationD
        currentObservationDay := observationE
        priorReleaseDay := 40
        currentReleaseDay := 50
        priorReleaseAt := 4014
        currentReleaseAt := 5014
        priorValueScaled := 98000
        currentValueScaled := 100000 }
    latestSameObservations :=
      { vintageDay := 80
        priorObservationDay := observationD
        currentObservationDay := observationE
        priorReleaseDay := 40
        currentReleaseDay := 50
        priorReleaseAt := 4014
        currentReleaseAt := 5014
        priorValueScaled := 103000
        currentValueScaled := 102000 }
    latestNaive :=
      { vintageDay := 80
        priorObservationDay := 55
        currentObservationDay := 58
        priorReleaseDay := 72
        currentReleaseDay := 73
        priorReleaseAt := 7214
        currentReleaseAt := 7314
        priorValueScaled := 20000
        currentValueScaled := 10000 }
    vintageDateAvailable := by decide
    releaseTimeStrictAvailable := by decide
    sameObservationDates := ⟨rfl, rfl⟩
    latestSamePostDecisionDay := by decide
    latestNaivePostDecisionDay := by decide
    latestNaiveObservationsPrecede := by decide
    vintageTurnoverCostBps := 1
    releaseTimeStrictTurnoverCostBps := 0
    revisionOnlyTurnoverCostBps := 0
    latestNaiveTurnoverCostBps := 1 }

def decisions : List RevisionLeakageDecision :=
  [decisionOne, decisionTwo, decisionThree, decisionFour]

/-- Required boundary: date-granular vintage validity does not imply exact
    release-time validity. -/
theorem first_transformation_is_vintage_valid_but_release_time_leaking :
    decisionOne.vintageDate.VintageValidButReleaseTimeLeaking
      decisionOne.asOfDay decisionOne.decisionAt := by
  decide

/-- Required nonleaking control: the second transformation is valid under both
    date-granular and exact release-time policies. -/
theorem second_transformation_is_valid_under_both_policies :
    decisionTwo.releaseTimeStrict.AvailableUnderBothPolicies
      decisionTwo.asOfDay decisionTwo.decisionAt := by
  decide

/-- Exact same-day boundary: the selected February value is released after the
    March 15 decision despite sharing its calendar day. -/
theorem first_decision_has_same_day_post_decision_input :
    decisionOne.vintageDate.HasSameDayPostDecisionInput
      decisionOne.asOfDay decisionOne.decisionAt := by
  decide

theorem controlled_vintage_date_total :
    totalVintageDateReturnBps decisions = -103 := by
  decide

theorem controlled_release_time_strict_total :
    totalReleaseTimeStrictReturnBps decisions = -23 := by
  decide

theorem controlled_revision_only_total :
    totalRevisionOnlyReturnBps decisions = 78 := by
  decide

theorem controlled_latest_naive_total :
    totalLatestNaiveReturnBps decisions = -44 := by
  decide

def certificate : RevisionLeakageStudyCertificate :=
  { studyId := "synthetic-alfred-release-and-revision-leakage"
    seriesId := "TESTREV"
    decisions := decisions
    vintageDateTotalReturnBps := -103
    releaseTimeStrictTotalReturnBps := -23
    revisionOnlyTotalReturnBps := 78
    latestNaiveTotalReturnBps := -44
    intradayReleaseLeakageBps := -80
    revisionOnlyLeakageBps := 101
    revisionPlusAvailabilityLeakageBps := -21
    vintageDateTotalCorrect := by decide
    releaseTimeStrictTotalCorrect := by decide
    revisionOnlyTotalCorrect := by decide
    latestNaiveTotalCorrect := by decide
    intradayLeakageCorrect := by decide
    revisionLeakageCorrect := by decide
    revisionPlusAvailabilityLeakageCorrect := by decide }

theorem strict_path_is_verified_point_in_time :
    certificate.StrictPointInTime :=
  certificate.strict_path_is_point_in_time

theorem intraday_release_boundary_changes_path_by_negative_eighty_bps :
    certificate.intradayReleaseLeakageBps = -80 := by
  decide

theorem pure_revision_counterfactual_adds_one_hundred_one_bps :
    certificate.revisionOnlyLeakageBps = 101 := by
  decide

theorem naive_latest_counterfactual_differs_by_negative_twenty_one_bps :
    certificate.revisionPlusAvailabilityLeakageBps = -21 := by
  decide

theorem latest_vintage_cannot_be_used_for_original_decision_day :
    ¬ decisionOne.latestSameObservations.vintageDay ≤
      decisionOne.asOfDay :=
  decisionOne.latest_same_vintage_is_not_available_on_decision_day

end LeanFinance.Examples.RevisionLeakage
