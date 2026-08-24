import LeanFinance.Execution.OrderLifecycle

namespace LeanFinance.Execution

inductive Side where
  | buy
  | sell
  deriving Repr, DecidableEq

structure Fill where
  fillId : Nat
  side : Side
  qty : Nat
  price : Nat
  fee : Nat
  deriving Repr, DecidableEq

namespace Fill

def signedQty (fill : Fill) : Int :=
  match fill.side with
  | .buy => Int.ofNat fill.qty
  | .sell => -Int.ofNat fill.qty

def cashDelta (fill : Fill) : Int :=
  let notional := Int.ofNat fill.qty * Int.ofNat fill.price
  match fill.side with
  | .buy => -notional - Int.ofNat fill.fee
  | .sell => notional - Int.ofNat fill.fee

end Fill

def totalFilledQty (fills : List Fill) : Nat :=
  fills.foldl (fun total fill => total + fill.qty) 0

def totalInventoryDelta (fills : List Fill) : Int :=
  fills.foldl (fun total fill => total + fill.signedQty) 0

def totalCashDelta (fills : List Fill) : Int :=
  fills.foldl (fun total fill => total + fill.cashDelta) 0

def fillIdsUnique (fills : List Fill) : Prop :=
  (fills.map (fun fill => fill.fillId)).Nodup

structure Reconciliation where
  initialCash : Int
  initialInventory : Int
  finalCash : Int
  finalInventory : Int
  fills : List Fill
  cashCorrect : finalCash = initialCash + totalCashDelta fills
  inventoryCorrect :
    finalInventory = initialInventory + totalInventoryDelta fills
  deriving Repr

structure ExecutionCertificate where
  authorization : OrderAuthorization
  lifecycle : List OrderState
  fills : List Fill
  authorizationAccepted : authorization.admissible = true
  lifecycleAccepted : lifecycleValid lifecycle = true
  reconciled : endsReconciled lifecycle = true
  uniqueFills : fillIdsUnique fills
  quantityBound : totalFilledQty fills ≤ authorization.authorizedQty
  reconciliation : Reconciliation
  reconciliationUsesFills : reconciliation.fills = fills
  deriving Repr

namespace ExecutionCertificate

theorem never_overfills
    (certificate : ExecutionCertificate) :
    totalFilledQty certificate.fills ≤
      certificate.authorization.authorizedQty :=
  certificate.quantityBound

theorem fill_identifiers_are_unique
    (certificate : ExecutionCertificate) :
    fillIdsUnique certificate.fills :=
  certificate.uniqueFills

theorem cash_is_conserved
    (certificate : ExecutionCertificate) :
    certificate.reconciliation.finalCash =
      certificate.reconciliation.initialCash +
        totalCashDelta certificate.reconciliation.fills :=
  certificate.reconciliation.cashCorrect

theorem inventory_is_conserved
    (certificate : ExecutionCertificate) :
    certificate.reconciliation.finalInventory =
      certificate.reconciliation.initialInventory +
        totalInventoryDelta certificate.reconciliation.fills :=
  certificate.reconciliation.inventoryCorrect

end ExecutionCertificate

end LeanFinance.Execution
