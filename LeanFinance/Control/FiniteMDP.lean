import LeanFinance.Core

namespace LeanFinance.Control

/-- One finitely represented successor of a state-action pair. `weight` is an
    unnormalized nonnegative transition weight; executable tools validate the
    complete finite kernel and normalize only when a value calculation needs it. -/
structure WeightedOutcome (State : Type) where
  nextState : State
  weight : Nat
  deriving Repr, DecidableEq

/-- Finite-support controlled dynamics. The formal safety layer reasons over
    every listed successor instead of trusting one sampled transition. -/
structure FiniteMDP (State Action : Type) where
  outcomes : State → Action → List (WeightedOutcome State)

namespace FiniteMDP

/-- An action is robustly one-step safe when every represented successor is in
    the declared safe set. -/
def RobustlySafe
    (model : FiniteMDP State Action)
    (safe : State → Prop)
    (state : State)
    (action : Action) : Prop :=
  ∀ outcome,
    outcome ∈ model.outcomes state action →
      safe outcome.nextState

/-- Executable Boolean checker used by generated finite certificates. -/
def robustlySafeBool
    (model : FiniteMDP State Action)
    (safe : State → Bool)
    (state : State)
    (action : Action) : Bool :=
  (model.outcomes state action).all
    (fun outcome => safe outcome.nextState)

/-- A successful Boolean check means every listed successor passed the safe-set
    predicate. -/
theorem robustlySafeBool_sound
    (model : FiniteMDP State Action)
    (safe : State → Bool)
    (state : State)
    (action : Action)
    (accepted : model.robustlySafeBool safe state action = true) :
    ∀ outcome,
      outcome ∈ model.outcomes state action →
        safe outcome.nextState = true := by
  simpa [robustlySafeBool] using accepted

/-- Integer numerator of a weighted one-step value. Division and calibration are
    intentionally left to the external exact checker. -/
def valueNumerator
    (model : FiniteMDP State Action)
    (value : State → Int)
    (state : State)
    (action : Action) : Int :=
  (model.outcomes state action).foldl
    (fun total outcome =>
      total + Int.ofNat outcome.weight * value outcome.nextState) 0

end FiniteMDP

end LeanFinance.Control
