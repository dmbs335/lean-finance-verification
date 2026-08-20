import LeanFinance.Core

namespace LeanFinance.Market

structure MarketMaker where
  inventory : Scalar
  inventoryLimit : Nat
  capital : Nat
  deriving Repr

def InventoryFeasible (maker : MarketMaker) : Prop :=
  -Int.ofNat maker.inventoryLimit ≤ maker.inventory ∧
    maker.inventory ≤ Int.ofNat maker.inventoryLimit

end LeanFinance.Market
