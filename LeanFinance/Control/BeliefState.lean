namespace LeanFinance.Control

/-- Finite hidden-state belief represented by nonnegative integer weights. The
    normalized probability is external; safety and robust value depend only on
    positive support. -/
structure FiniteBelief (Hidden : Type) where
  weight : Hidden → Nat

namespace FiniteBelief

def Supported (belief : FiniteBelief Hidden) (hidden : Hidden) : Prop :=
  0 < belief.weight hidden

end FiniteBelief

/-- Observation likelihood weights for a finite hidden-state model. -/
structure ObservationKernel (Hidden Observation : Type) where
  likelihood : Observation → Hidden → Nat

/-- Unnormalized Bayes update. Normalization does not change positive support. -/
def posterior
    (prior : FiniteBelief Hidden)
    (kernel : ObservationKernel Hidden Observation)
    (observation : Observation) : FiniteBelief Hidden :=
  { weight := fun hidden =>
      prior.weight hidden * kernel.likelihood observation hidden }

theorem zero_likelihood_eliminates_hypothesis
    (prior : FiniteBelief Hidden)
    (kernel : ObservationKernel Hidden Observation)
    (observation : Observation)
    (hidden : Hidden)
    (zeroLikelihood : kernel.likelihood observation hidden = 0) :
    (posterior prior kernel observation).weight hidden = 0 := by
  simp [posterior, zeroLikelihood]

theorem zero_prior_remains_zero
    (prior : FiniteBelief Hidden)
    (kernel : ObservationKernel Hidden Observation)
    (observation : Observation)
    (hidden : Hidden)
    (zeroPrior : prior.weight hidden = 0) :
    (posterior prior kernel observation).weight hidden = 0 := by
  simp [posterior, zeroPrior]

/-- Positive support under one belief is contained in another. -/
def SupportRefines
    (refined outer : FiniteBelief Hidden) : Prop :=
  ∀ hidden, refined.Supported hidden → outer.Supported hidden

/-- A lower bound over every hidden state still supported by a belief. -/
def LowerBoundOnBelief
    (belief : FiniteBelief Hidden)
    (value : Hidden → Int)
    (bound : Int) : Prop :=
  ∀ hidden, belief.Supported hidden → bound ≤ value hidden

def GreatestBeliefLowerBound
    (belief : FiniteBelief Hidden)
    (value : Hidden → Int)
    (bound : Int) : Prop :=
  LowerBoundOnBelief belief value bound ∧
    ∀ candidate,
      LowerBoundOnBelief belief value candidate → candidate ≤ bound

/-- Removing hidden-state hypotheses cannot reduce the greatest robust lower
    value for a fixed action. -/
theorem belief_refinement_improves_robust_lower_bound
    (refined outer : FiniteBelief Hidden)
    (value : Hidden → Int)
    (outerLower refinedLower : Int)
    (refines : SupportRefines refined outer)
    (outerGreatest : GreatestBeliefLowerBound outer value outerLower)
    (refinedGreatest :
      GreatestBeliefLowerBound refined value refinedLower) :
    outerLower ≤ refinedLower := by
  apply refinedGreatest.2
  intro hidden supported
  exact outerGreatest.1 hidden (refines hidden supported)

/-- An action is safe for a belief when it is safe in every supported hidden
    state. -/
def RobustlySafeOnBelief
    (belief : FiniteBelief Hidden)
    (safe : Hidden → Action → Prop)
    (action : Action) : Prop :=
  ∀ hidden, belief.Supported hidden → safe hidden action

end LeanFinance.Control
