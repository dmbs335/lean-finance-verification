import LeanFinance.GameTheory.Action

namespace LeanFinance.Market

structure Order where
  traderId : Nat
  quantity : Rat
  price : Rat
  isBuy : Bool

end LeanFinance.Market
