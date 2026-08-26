import LeanFinance.PnL.Closure

namespace LeanFinance.PnL.Example

open LeanFinance.PnL

def quadraticModel : QuadraticValue :=
  { constant := 0
    linear := 10
    quadratic := 2 }

theorem controlled_realized_change_is_twenty_eight :
    quadraticModel.realizedChange 0 2 = 28 := by
  decide

theorem controlled_attribution_closes_exactly :
    quadraticModel.realizedChange 0 2 =
      quadraticModel.firstOrder 0 2 +
        quadraticModel.secondOrder 2 :=
  quadraticModel.exact_quadratic_closure 0 2

def closedExplanation : Explanation :=
  { realizedPnL := 28
    attributions := [20, 8]
    residual := 0
    residualTolerance := 0
    localGreeksValid := true
    localMarketMoveValid := true
    localResultValid := true
    positionBound := true
    modelBound := true
    valuationTimeBound := true
    formulaBound := true
    accounting := by decide }

theorem exact_quadratic_explanation_is_closed :
    closedExplanation.status = .closed := by
  decide

def partialExplanation : Explanation :=
  { realizedPnL := 35
    attributions := [20, 8]
    residual := 7
    residualTolerance := 3
    localGreeksValid := true
    localMarketMoveValid := true
    localResultValid := true
    positionBound := true
    modelBound := true
    valuationTimeBound := true
    formulaBound := true
    accounting := by decide }

theorem material_residual_is_partial :
    partialExplanation.status = .partial := by
  decide

def modelSubstitutedExplanation : Explanation :=
  { realizedPnL := 28
    attributions := [20, 8]
    residual := 0
    residualTolerance := 0
    localGreeksValid := true
    localMarketMoveValid := true
    localResultValid := true
    positionBound := true
    modelBound := false
    valuationTimeBound := true
    formulaBound := true
    accounting := by decide }

theorem zero_residual_with_model_mismatch_is_open :
    modelSubstitutedExplanation.status = .open := by
  decide

end LeanFinance.PnL.Example
