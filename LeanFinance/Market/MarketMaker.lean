import LeanFinance.Market.Order
import LeanFinance.Market.Liquidity

namespace LeanFinance

structure MarketMaker where
  inventory : Rat
  riskLimit : Rat


def inventoryConstraint (mm : MarketMaker) : Prop :=
  |mm.inventory| <= mm.riskLimit

end LeanFinance
