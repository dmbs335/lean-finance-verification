import LeanFinance.Epistemic.SemanticsVersionSpace

namespace LeanFinance.Generated.CostModelSemanticsVersionSpace

open LeanFinance.Epistemic

structure State where
  baselineExecuted : Bool
  resultPublished : Bool
  costModelTampered : Bool
  deriving Repr, DecidableEq

def broadHypothesis : ActionSemanticsHypothesis State :=
  {
    enabled := fun state =>
      state.baselineExecuted && !state.resultPublished
    transition := fun state =>
      { state with costModelTampered := true }
  }

def singleUseHypothesis : ActionSemanticsHypothesis State :=
  {
    enabled := fun state =>
      state.baselineExecuted &&
        !state.resultPublished &&
          !state.costModelTampered
    transition := fun state =>
      { state with costModelTampered := true }
  }

def candidates : List (ActionSemanticsHypothesis State) :=
  [broadHypothesis, singleUseHypothesis]

def positive : List (PositiveActionObservation State) :=
  [
    {
      before :=
        {
          baselineExecuted := true
          resultPublished := false
          costModelTampered := false
        }
      after :=
        {
          baselineExecuted := true
          resultPublished := false
          costModelTampered := true
        }
    }
  ]

def negative : List (NegativeActionObservation State) :=
  [
    {
      state :=
        {
          baselineExecuted := false
          resultPublished := false
          costModelTampered := false
        }
    },
    {
      state :=
        {
          baselineExecuted := true
          resultPublished := true
          costModelTampered := false
        }
    }
  ]

theorem broad_remains_consistent :
    ActionVersionSpace candidates positive negative broadHypothesis := by
  simp [ActionVersionSpace, ConsistentWithActionObservations,
    ConsistentWithPositive, ConsistentWithNegative,
    candidates, positive, negative, broadHypothesis]

theorem single_use_remains_consistent :
    ActionVersionSpace candidates positive negative singleUseHypothesis := by
  simp [ActionVersionSpace, ConsistentWithActionObservations,
    ConsistentWithPositive, ConsistentWithNegative,
    candidates, positive, negative, singleUseHypothesis]

def probe : State :=
  {
    baselineExecuted := true
    resultPublished := false
    costModelTampered := true
  }

def distinguishingProbe :
    DistinguishingProbe candidates positive negative :=
  {
    probe := probe
    left := broadHypothesis
    right := singleUseHypothesis
    leftConsistent := broad_remains_consistent
    rightConsistent := single_use_remains_consistent
    separates := by
      apply Or.inl
      decide
  }

theorem current_traces_do_not_identify_one_semantics :
    broadHypothesis ≠ singleUseHypothesis :=
  distinguishingProbe.witnesses_semantics_ambiguity

end LeanFinance.Generated.CostModelSemanticsVersionSpace
