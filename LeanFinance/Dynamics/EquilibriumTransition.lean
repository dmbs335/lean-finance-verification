import LeanFinance.Types

namespace LeanFinance.Dynamics

inductive Regime
  | stable
  | stressed
  | crisis
  deriving DecidableEq, Repr

structure EquilibriumState where
  price : Scalar
  stability : Scalar
  regime : Regime
  deriving Repr

structure EquilibriumTransition where
  move : EquilibriumState → EquilibriumState

def transition
    (dynamics : EquilibriumTransition)
    (state : EquilibriumState) : EquilibriumState :=
  dynamics.move state

def IsFixedPoint
    (dynamics : EquilibriumTransition)
    (state : EquilibriumState) : Prop :=
  transition dynamics state = state

def identityEquilibriumTransition : EquilibriumTransition :=
  { move := fun state => state }

theorem identityEquilibriumTransition_fixed (state : EquilibriumState) :
    IsFixedPoint identityEquilibriumTransition state :=
  rfl

end LeanFinance.Dynamics
