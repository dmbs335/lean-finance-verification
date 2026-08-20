import LeanFinance.Market.OrderFlow

namespace LeanFinance.Market

structure PriceImpact where
  lambda : Scalar
  deriving Repr

def PriceImpact.WellFormed (impact : PriceImpact) : Prop :=
  0 <= impact.lambda

def priceChange (impact : PriceImpact) (flow : OrderFlow) : Scalar :=
  impact.lambda * flow.totalFlow

def nextPrice
    (currentPrice : Scalar)
    (impact : PriceImpact)
    (flow : OrderFlow) : Scalar :=
  currentPrice + priceChange impact flow

end LeanFinance.Market
