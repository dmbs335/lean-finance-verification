import LeanFinance.PnL.Closure

namespace LeanFinance.PnL.Example

open LeanFinance.PnL

def binding : AttributionBinding :=
  { portfolioHash := "portfolio-example"
    marketDataBeforeHash := "market-before"
    marketDataAfterHash := "market-after"
    modelId := "quadratic-example"
    modelVersion := "v1"
    valuationBefore := 0
    valuationAfter := 2 }

def quadraticFactor : LocalQuadraticAttribution :=
  { factorId := "controlled-quadratic"
    baseValue := 0
    firstSensitivity := 10
    halfSecondSensitivity := 2
    marketMove := 2
    claimedFirstOrderPnl := 20
    claimedSecondOrderPnl := 8
    availableAt := 2
    binding := binding }

theorem controlled_first_order_is_twenty :
    quadraticFactor.firstOrderPnl = 20 := by
  decide

theorem controlled_second_order_is_eight :
    quadraticFactor.secondOrderPnl = 8 := by
  decide

theorem controlled_attribution_closes_exactly :
    quadraticFactor.modeledAfterValue - quadraticFactor.baseValue =
      quadraticFactor.explainedPnl :=
  quadraticFactor.exact_local_quadratic_closure

def zeroNonMarket : NonMarketPnl :=
  { carry := 0
    trades := 0
    cashflows := 0
    transactionCost := 0
    modelRevision := 0 }

def closedExplanation : PnlExplain :=
  { explanationId := "quadratic-closed"
    decisionAt := 2
    tolerance := 0
    binding := binding
    factors := [quadraticFactor]
    nonMarket := zeroNonMarket
    result :=
      { realizedPnl := 28
        generatedAt := 2
        binding := binding } }

theorem exact_quadratic_explanation_is_closed :
    closedExplanation.Closed := by
  unfold PnlExplain.Closed PnlExplain.LocalAndBindingValid
  decide

def partialExplanation : PnlExplain :=
  { closedExplanation with
    explanationId := "quadratic-partial"
    tolerance := 3
    result :=
      { realizedPnl := 35
        generatedAt := 2
        binding := binding } }

theorem material_residual_is_partial :
    partialExplanation.Partial := by
  unfold PnlExplain.Partial PnlExplain.LocalAndBindingValid
  decide

def substitutedBinding : AttributionBinding :=
  { binding with modelVersion := "v2" }

def substitutedFactor : LocalQuadraticAttribution :=
  { quadraticFactor with binding := substitutedBinding }

def modelSubstitutedExplanation : PnlExplain :=
  { closedExplanation with
    explanationId := "quadratic-open-model-substitution"
    factors := [substitutedFactor] }

theorem zero_residual_with_model_mismatch_is_open :
    modelSubstitutedExplanation.Open := by
  unfold PnlExplain.Open PnlExplain.LocalAndBindingValid
  decide

end LeanFinance.PnL.Example
