import LeanFinance.Core
import LeanFinance.GameTheory.Player
import LeanFinance.GameTheory.Action

namespace LeanFinance.GameTheory

structure PayoffModel where
  valueWeight : Scalar
  inventoryPenalty : Scalar
  benchmarkPenalty : Scalar
  deriving Repr

def signedQuantity (action : Action) : Scalar :=
  match action.side with
  | Side.buy => Int.ofNat action.quantity
  | Side.hold => 0
  | Side.sell => -Int.ofNat action.quantity

def utility
    (model : PayoffModel)
    (player : Player)
    (fundamental price inventory benchmarkGap : Scalar)
    (action : Action) : Scalar :=
  let q := signedQuantity action
  model.valueWeight * (fundamental - price) * q
    - (Int.ofNat player.riskAversion + model.inventoryPenalty) * inventory * q
    - model.benchmarkPenalty * benchmarkGap * q

end LeanFinance.GameTheory
