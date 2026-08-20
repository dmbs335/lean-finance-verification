import LeanFinance.Inference.Identification

namespace LeanFinance.Inference

/-- A finite abstraction used to demonstrate the inverse-game identification
    boundary. Real estimators may replace these buckets with richer states. -/
structure InverseGameState where
  publicFlowBucket : Nat
  hiddenPayoffType : Nat
  constraintBinding : Bool
  deriving DecidableEq, Repr

def coarseObservation (state : InverseGameState) : Nat :=
  state.publicFlowBucket

def publicFlowTarget (state : InverseGameState) : Nat :=
  state.publicFlowBucket

def hiddenPayoffTarget (state : InverseGameState) : Nat :=
  state.hiddenPayoffType

def constraintBindingTarget (state : InverseGameState) : Bool :=
  state.constraintBinding

def observationallyEquivalentStateA : InverseGameState :=
  {
    publicFlowBucket := 7
    hiddenPayoffType := 0
    constraintBinding := true
  }

def observationallyEquivalentStateB : InverseGameState :=
  {
    publicFlowBucket := 7
    hiddenPayoffType := 1
    constraintBinding := true
  }

/-- Aggregate order flow alone cannot identify the primitive payoff type:
    distinct payoff types can generate the same public-flow observation. -/
theorem hiddenPayoff_not_identified_by_coarseObservation :
    ¬ Identified coarseObservation hiddenPayoffTarget := by
  apply not_identified_of_counterexample
    coarseObservation
    hiddenPayoffTarget
    observationallyEquivalentStateA
    observationallyEquivalentStateB
  · rfl
  · decide

/-- The public-flow bucket itself is, trivially but importantly, identified by
    the coarse observation. -/
theorem publicFlow_identified_by_coarseObservation :
    Identified coarseObservation publicFlowTarget := by
  apply identified_of_factorization
    coarseObservation
    publicFlowTarget
    (fun observation => observation)
  intro state
  rfl

structure ConstraintObservation where
  publicFlowBucket : Nat
  constraintBinding : Bool
  deriving DecidableEq, Repr

def enrichedObservation
    (state : InverseGameState) : ConstraintObservation :=
  {
    publicFlowBucket := state.publicFlowBucket
    constraintBinding := state.constraintBinding
  }

def forgetConstraintObservation
    (observation : ConstraintObservation) : Nat :=
  observation.publicFlowBucket

theorem coarseObservation_refinedBy_enrichedObservation
    (state : InverseGameState) :
    coarseObservation state =
      forgetConstraintObservation (enrichedObservation state) :=
  rfl

/-- Adding a valid constraint proxy refines the flow observation and therefore
    preserves identification of every target already identified by flow. -/
theorem publicFlow_identified_by_enrichedObservation :
    Identified enrichedObservation publicFlowTarget :=
  identified_of_observation_refinement
    coarseObservation
    enrichedObservation
    forgetConstraintObservation
    publicFlowTarget
    coarseObservation_refinedBy_enrichedObservation
    publicFlow_identified_by_coarseObservation

/-- Constraint activity becomes point identified once the public observation
    explicitly contains a valid binding-constraint proxy. -/
theorem constraintBinding_identified_by_enrichedObservation :
    Identified enrichedObservation constraintBindingTarget := by
  apply identified_of_factorization
    enrichedObservation
    constraintBindingTarget
    (fun observation => observation.constraintBinding)
  intro state
  rfl

/-- The formal target of inverse-game research should therefore be an
    identifiable functional of the equivalence class, not necessarily the
    complete latent primitive. -/
theorem constraintSignal_remains_identified_after_labeling
    (label : Bool → String) :
    Identified enrichedObservation
      (fun state => label (constraintBindingTarget state)) :=
  identified_postprocess
    constraintBinding_identified_by_enrichedObservation
    label

end LeanFinance.Inference
