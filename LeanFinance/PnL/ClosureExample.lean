import LeanFinance.PnL.Closure

namespace LeanFinance.PnL.ClosureExample

open LeanFinance.PnL

def canonicalBinding : AttributionBinding :=
  { portfolioHash := "portfolio-p1"
    marketDataBeforeHash := "market-before-a"
    marketDataAfterHash := "market-after-b"
    modelId := "risk-model-x"
    modelVersion := "v1"
    valuationBefore := 10
    valuationAfter := 20 }

def deltaGamma : LocalQuadraticAttribution :=
  { factorId := "delta-gamma"
    baseValue := 1000
    firstSensitivity := 10
    halfSecondSensitivity := 2
    marketMove := 3
    claimedFirstOrderPnl := 30
    claimedSecondOrderPnl := 18
    availableAt := 20
    binding := canonicalBinding }

def vegaConvexity : LocalQuadraticAttribution :=
  { factorId := "vega-convexity"
    baseValue := 500
    firstSensitivity := -4
    halfSecondSensitivity := 1
    marketMove := 2
    claimedFirstOrderPnl := -8
    claimedSecondOrderPnl := 4
    availableAt := 20
    binding := canonicalBinding }

def nonMarket : NonMarketPnl :=
  { carry := 6
    trades := 5
    cashflows := 10
    transactionCost := 7
    modelRevision := 2 }

def closedExplanation : PnlExplain :=
  { explanationId := "controlled-closed"
    decisionAt := 20
    tolerance := 2
    binding := canonicalBinding
    factors := [deltaGamma, vegaConvexity]
    nonMarket := nonMarket
    result :=
      { realizedPnl := 61
        generatedAt := 20
        binding := canonicalBinding } }

theorem delta_gamma_exactly_closes_locally :
    deltaGamma.modeledAfterValue - deltaGamma.baseValue =
      deltaGamma.explainedPnl :=
  deltaGamma.exact_local_quadratic_closure

theorem controlled_reconstruction_is_sixty :
    closedExplanation.reconstructedPnl = 60 := by
  decide

theorem controlled_residual_is_one :
    closedExplanation.residual = 1 := by
  decide

def closedCertificate : PnlExplainClosureCertificate :=
  { explain := closedExplanation
    closed := by
      unfold PnlExplain.Closed PnlExplain.LocalAndBindingValid
      decide }

def partialExplanation : PnlExplain :=
  { closedExplanation with
    explanationId := "controlled-partial"
    result :=
      { realizedPnl := 70
        generatedAt := 20
        binding := canonicalBinding } }

theorem material_residual_is_partial :
    partialExplanation.Partial := by
  unfold PnlExplain.Partial PnlExplain.LocalAndBindingValid
  decide

def substitutedBinding : AttributionBinding :=
  { canonicalBinding with portfolioHash := "portfolio-substituted" }

def locallyCorrectButSubstituted : LocalQuadraticAttribution :=
  { deltaGamma with binding := substitutedBinding }

def openExplanation : PnlExplain :=
  { closedExplanation with
    explanationId := "controlled-open-binding"
    factors := [locallyCorrectButSubstituted, vegaConvexity]
    result :=
      { realizedPnl := 61
        generatedAt := 20
        binding := canonicalBinding } }

theorem substituted_factor_is_locally_formula_correct :
    locallyCorrectButSubstituted.FormulaValid = true := by
  decide

theorem local_formula_correctness_does_not_imply_global_binding :
    locallyCorrectButSubstituted.BoundTo canonicalBinding = false := by
  decide

theorem binding_failure_keeps_explanation_open :
    openExplanation.Open := by
  unfold PnlExplain.Open PnlExplain.LocalAndBindingValid
  decide

end LeanFinance.PnL.ClosureExample
