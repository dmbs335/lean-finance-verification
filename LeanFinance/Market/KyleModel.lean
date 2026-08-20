import LeanFinance.Market.OrderFlow
import LeanFinance.Market.PriceFormation

namespace LeanFinance

structure KyleModel where
  lambda : Rat
  privateSignalVariance : Rat
  noiseVariance : Rat


def kylePriceImpact (model : KyleModel) (flow : OrderFlow) : Rat :=
  model.lambda * (flow.informed + flow.noise)

end LeanFinance
