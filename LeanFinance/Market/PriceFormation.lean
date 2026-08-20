import LeanFinance.Market.OrderFlow

namespace LeanFinance.Market

structure PriceImpact where
  lambda : Rat

 def priceChange (impact : PriceImpact) (flow : OrderFlow) : Rat :=
  impact.lambda * flow.totalFlow

end LeanFinance.Market
