import LeanFinance.Execution.Ledger

namespace LeanFinance.Execution.Example

open LeanFinance.Execution
open LeanFinance.Control

def authorization : OrderAuthorization :=
  { orderId := "controlled-buy"
    authority := .microAutonomy
    capitalCapUnits := 100
    authorizedQty := 100 }

def lifecycle : List OrderState :=
  [.proposed, .shielded, .authorized, .submitted, .acknowledged,
    .partiallyFilled, .filled, .reconciled]

def fills : List Fill :=
  [ { fillId := 1, side := .buy, qty := 40, price := 10, fee := 1 }
  , { fillId := 2, side := .buy, qty := 60, price := 10, fee := 1 } ]

def reconciliation : Reconciliation :=
  { initialCash := 10000
    initialInventory := 0
    finalCash := 8998
    finalInventory := 100
    fills := fills
    cashCorrect := by decide
    inventoryCorrect := by decide }

def certificate : ExecutionCertificate :=
  { authorization := authorization
    lifecycle := lifecycle
    fills := fills
    authorizationAccepted := by decide
    lifecycleAccepted := by decide
    reconciled := by decide
    uniqueFills := by decide
    quantityBound := by decide
    reconciliation := reconciliation
    reconciliationUsesFills := rfl }

theorem controlled_order_fills_exactly_authorized_quantity :
    totalFilledQty certificate.fills =
      certificate.authorization.authorizedQty := by
  decide

theorem controlled_cash_delta_is_negative_one_thousand_two :
    totalCashDelta certificate.fills = -1002 := by
  decide

theorem controlled_inventory_delta_is_one_hundred :
    totalInventoryDelta certificate.fills = 100 := by
  decide

theorem revoked_fixture_cannot_submit :
    ({ orderId := "revoked", authority := .revoked,
       capitalCapUnits := 100, authorizedQty := 10 } : OrderAuthorization).admissible =
      false := by
  decide

end LeanFinance.Execution.Example
