import LeanFinance.Market.Order

namespace LeanFinance.Market

structure OrderFlow where
  informed : Rat
  noise : Rat

 def totalFlow (o : OrderFlow) : Rat :=
  o.informed + o.noise

end LeanFinance.Market
