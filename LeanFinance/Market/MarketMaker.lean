import LeanFinance.Types

namespace LeanFinance.Market

structure MarketMaker where
  inventory : Scalar
  riskLimit : Scalar
  deriving Repr

def MarketMaker.WellFormed (maker : MarketMaker) : Prop :=
  0 <= maker.riskLimit

def inventoryConstraint (maker : MarketMaker) : Prop :=
  -maker.riskLimit <= maker.inventory ∧
  maker.inventory <= maker.riskLimit

end LeanFinance.Market
