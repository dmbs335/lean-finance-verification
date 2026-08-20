import LeanFinance.Core
import LeanFinance.Market.PriceFormation

namespace LeanFinance.Market

structure KyleModel where
  priorPrice : Scalar
  impact : LinearPriceImpact
  deriving Repr

def KyleModel.quote
    (model : KyleModel)
    (flow : OrderFlow) : Scalar :=
  nextPrice model.priorPrice model.impact flow

theorem quote_at_zero_flow
    (model : KyleModel)
    (flow : OrderFlow)
    (h : flow.total = 0) :
    model.quote flow = model.priorPrice := by
  simp [KyleModel.quote, nextPrice, priceChange, h]

end LeanFinance.Market
