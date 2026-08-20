import LeanFinance.Market.PriceFormation

namespace LeanFinance.Market

structure KyleModel where
  impact : PriceImpact
  privateSignalVariance : Scalar
  noiseVariance : Scalar
  deriving Repr

def KyleModel.WellFormed (model : KyleModel) : Prop :=
  model.impact.WellFormed ∧
  0 <= model.privateSignalVariance ∧
  0 < model.noiseVariance

def kylePriceImpact (model : KyleModel) (flow : OrderFlow) : Scalar :=
  priceChange model.impact flow

theorem kylePriceImpact_def (model : KyleModel) (flow : OrderFlow) :
    kylePriceImpact model flow = model.impact.lambda * flow.totalFlow :=
  rfl

end LeanFinance.Market
