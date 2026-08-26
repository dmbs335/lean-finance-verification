import LeanFinance.Backtest.TemporalNoninterference

namespace LeanFinance.Backtest.TemporalNoninterferenceExample

open LeanFinance.Backtest

/-- A small analogue of a date-indexed market series: observations through day 5
    are the decision-time prefix, while day 15 is a later extension. -/
inductive PriceKey where
  | janTwo
  | janFive
  | janFifteen
  deriving Repr, DecidableEq

def availableAt : PriceKey → Timestamp
  | .janTwo => 2
  | .janFive => 5
  | .janFifteen => 15

def baseHistory : PriceKey → Option Int
  | .janTwo => some 100
  | .janFive => some 103
  | .janFifteen => none

def futureExtendedHistory : PriceKey → Option Int
  | .janTwo => some 100
  | .janFive => some 103
  | .janFifteen => some 999

theorem histories_match_through_day_six :
    HistoryPrefixEquivalent availableAt
      baseHistory futureExtendedHistory 6 := by
  intro key available
  cases key <;>
    simp [availableAt, baseHistory, futureExtendedHistory] at available ⊢

def valueOrZero : Option Int → Int
  | some value => value
  | none => 0

/-- Past-only lookup. It uses the latest key whose availability is no later than
    the cutoff. -/
def causalForwardFill
    (history : PriceKey → Option Int)
    (cutoff : Timestamp) : Int :=
  if h15 : 15 ≤ cutoff then
    valueOrZero (history .janFifteen)
  else if h5 : 5 ≤ cutoff then
    valueOrZero (history .janFive)
  else if h2 : 2 ≤ cutoff then
    valueOrZero (history .janTwo)
  else
    0

theorem causal_forward_fill_is_temporally_noninterfering :
    TemporalNoninterference availableAt causalForwardFill := by
  intro cutoff left right samePrefix
  by_cases h15 : 15 ≤ cutoff
  · have same := samePrefix .janFifteen h15
    simp [causalForwardFill, h15, same]
  · by_cases h5 : 5 ≤ cutoff
    · have same := samePrefix .janFive h5
      simp [causalForwardFill, h15, h5, same]
    · by_cases h2 : 2 ≤ cutoff
      · have same := samePrefix .janTwo h2
        simp [causalForwardFill, h15, h5, h2, same]
      · simp [causalForwardFill, h15, h5, h2]

/-- Append-tail forward fill mirrors the dangerous semantic shape in which a
    missing query is appended after the complete series and receives its final
    value, including values from after the decision cutoff. -/
def appendTailForwardFill
    (history : PriceKey → Option Int)
    (_cutoff : Timestamp) : Int :=
  valueOrZero (history .janFifteen)

def appendTailCounterexample :
    TemporalCounterexample availableAt appendTailForwardFill :=
  { cutoff := 6
    left := baseHistory
    right := futureExtendedHistory
    sameAvailablePrefix := histories_match_through_day_six
    outputDifferent := by decide }

theorem append_tail_fill_violates_temporal_noninterference :
    ¬ TemporalNoninterference availableAt appendTailForwardFill :=
  appendTailCounterexample.not_temporally_noninterfering

def thresholdPosition (value : Int) : Int :=
  if 500 ≤ value then 1 else -1

/-- A deterministic decision rule remains safe when fed by the causal source. -/
theorem causal_position_is_temporally_noninterfering :
    TemporalNoninterference availableAt
      (fun history cutoff =>
        thresholdPosition (causalForwardFill history cutoff)) :=
  pointwise_postprocessing_preserves_noninterference
    availableAt causalForwardFill thresholdPosition
    causal_forward_fill_is_temporally_noninterfering

theorem unsafe_fill_reverses_the_controlled_position :
    thresholdPosition (appendTailForwardFill baseHistory 6) = -1 ∧
      thresholdPosition
        (appendTailForwardFill futureExtendedHistory 6) = 1 := by
  decide

end LeanFinance.Backtest.TemporalNoninterferenceExample
