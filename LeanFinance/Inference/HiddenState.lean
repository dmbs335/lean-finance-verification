import LeanFinance.Types

namespace LeanFinance.Inference

structure HiddenMarketState where
  position : Scalar
  leverage : Scalar
  liquidityState : Scalar
  constraintSlack : Scalar
  deriving Repr

structure Observation where
  price : Scalar
  volume : Scalar
  orderFlow : Scalar
  deriving DecidableEq, Repr

structure ObservationModel where
  predict : HiddenMarketState → Observation

def Compatible
    (model : ObservationModel)
    (state : HiddenMarketState)
    (observation : Observation) : Prop :=
  model.predict state = observation

theorem predictedObservationCompatible
    (model : ObservationModel)
    (state : HiddenMarketState) :
    Compatible model state (model.predict state) :=
  rfl

end LeanFinance.Inference
