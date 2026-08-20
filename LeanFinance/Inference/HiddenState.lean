import LeanFinance.GameTheory.Belief
import LeanFinance.Market.OrderFlow

namespace LeanFinance

structure HiddenMarketState where
  position : Rat
  leverage : Rat
  liquidityState : Rat

structure Observation where
  price : Rat
  volume : Rat


def compatible (s : HiddenMarketState) (o : Observation) : Prop :=
  True

end LeanFinance
