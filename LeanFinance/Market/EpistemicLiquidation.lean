namespace LeanFinance.Market

/-- A market shock caused by loss of confidence in research validity. -/
structure EpistemicShock where
  evidenceDebtIncrease : Nat
  trustReduction : Nat
  deriving Repr

/-- Allocation response to evidence confidence changes. -/
structure CapitalResponse where
  capitalBefore : Nat
  capitalAfter : Nat
  deriving Repr

namespace CapitalResponse

def Liquidation (response : CapitalResponse) : Prop :=
  response.capitalAfter ≤ response.capitalBefore

theorem confidence_shock_can_reduce_allocation
    (response : CapitalResponse)
    (h : response.Liquidation) :
    response.capitalAfter ≤ response.capitalBefore :=
  h

end CapitalResponse

end LeanFinance.Market
