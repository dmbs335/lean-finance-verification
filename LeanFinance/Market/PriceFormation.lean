import LeanFinance.Core
import LeanFinance.Market.OrderFlow

namespace LeanFinance.Market

structure LinearPriceImpact where
  coefficient : Scalar
  deriving Repr

def priceChange
    (impact : LinearPriceImpact)
    (flow : OrderFlow) : Scalar :=
  impact.coefficient * flow.total

def nextPrice
    (currentPrice : Scalar)
    (impact : LinearPriceImpact)
    (flow : OrderFlow) : Scalar :=
  currentPrice + priceChange impact flow

theorem zero_flow_no_price_change
    (impact : LinearPriceImpact)
    (flow : OrderFlow)
    (h : flow.total = 0) :
    priceChange impact flow = 0 := by
  simp [priceChange, h]

end LeanFinance.Market
