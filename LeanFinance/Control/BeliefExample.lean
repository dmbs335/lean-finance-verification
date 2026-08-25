import LeanFinance.Control.BeliefState

namespace LeanFinance.Control.BeliefExample

open LeanFinance.Control

inductive Hidden where
  | bull
  | base
  | bear
  deriving Repr, DecidableEq

inductive Observation where
  | stable
  | stress
  deriving Repr, DecidableEq

inductive Action where
  | hold
  | increase
  | reduce
  deriving Repr, DecidableEq

def prior : FiniteBelief Hidden :=
  { weight := fun
      | .bull => 2
      | .base => 5
      | .bear => 3 }

def kernel : ObservationKernel Hidden Observation :=
  { likelihood := fun observation hidden =>
      match observation, hidden with
      | .stable, .bull => 4
      | .stable, .base => 2
      | .stable, .bear => 0
      | .stress, .bull => 0
      | .stress, .base => 1
      | .stress, .bear => 4 }

def stableBelief : FiniteBelief Hidden :=
  posterior prior kernel .stable

def stressBelief : FiniteBelief Hidden :=
  posterior prior kernel .stress

theorem stable_removes_bear :
    stableBelief.weight .bear = 0 := by
  decide

theorem stress_removes_bull :
    stressBelief.weight .bull = 0 := by
  decide

theorem stable_refines_prior : SupportRefines stableBelief prior := by
  intro hidden supported
  cases hidden <;>
    simp [FiniteBelief.Supported, stableBelief, posterior, prior, kernel]
      at supported ⊢

def increaseValue : Hidden → Int
  | .bull => 9
  | .base => 5
  | .bear => -11

theorem prior_increase_lower_is_negative_eleven :
    GreatestBeliefLowerBound prior increaseValue (-11) := by
  constructor
  · intro hidden _supported
    cases hidden <;> decide
  · intro candidate lower
    have witness := lower .bear (by
      simp [FiniteBelief.Supported, prior])
    simpa [increaseValue] using witness

theorem stable_increase_lower_is_five :
    GreatestBeliefLowerBound stableBelief increaseValue 5 := by
  constructor
  · intro hidden supported
    cases hidden with
    | bull => decide
    | base => decide
    | bear =>
        have impossible : False := by
          simpa [FiniteBelief.Supported, stableBelief, posterior, prior,
            kernel] using supported
        exact False.elim impossible
  · intro candidate lower
    have witness := lower .base (by
      simp [FiniteBelief.Supported, stableBelief, posterior, prior, kernel])
    simpa [increaseValue] using witness

theorem stable_observation_raises_increase_lower_bound :
    (-11 : Int) ≤ 5 :=
  belief_refinement_improves_robust_lower_bound
    stableBelief prior increaseValue (-11) 5
    stable_refines_prior
    prior_increase_lower_is_negative_eleven
    stable_increase_lower_is_five

end LeanFinance.Control.BeliefExample
