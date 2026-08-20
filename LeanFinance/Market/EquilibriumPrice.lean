import LeanFinance.Core

namespace LeanFinance.Market

structure DemandSupply where
  demand : Nat
  supply : Nat
  deriving Repr

def ClearsAt (_price : Scalar) (book : DemandSupply) : Prop :=
  book.demand = book.supply

theorem clearing_is_balanced
    (price : Scalar)
    (book : DemandSupply)
    (h : ClearsAt price book) : book.demand = book.supply :=
  h

end LeanFinance.Market
