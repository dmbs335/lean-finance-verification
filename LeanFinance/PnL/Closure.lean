import LeanFinance.Core

namespace LeanFinance.PnL

/-- Identity shared by every local attribution and by the realized PnL result.
    Local arithmetic is not globally meaningful unless all objects refer to the
    same portfolio, market snapshots, model version, and valuation interval. -/
structure AttributionBinding where
  portfolioHash : ContentHash
  marketDataBeforeHash : ContentHash
  marketDataAfterHash : ContentHash
  modelId : String
  modelVersion : String
  valuationBefore : Timestamp
  valuationAfter : Timestamp
  deriving Repr, DecidableEq

namespace AttributionBinding

/-- Minimal structural obligations for a binding identity. -/
def WellFormed (binding : AttributionBinding) : Bool :=
  decide (
    NonEmptyString binding.portfolioHash ∧
      NonEmptyString binding.marketDataBeforeHash ∧
        NonEmptyString binding.marketDataAfterHash ∧
          NonEmptyString binding.modelId ∧
            NonEmptyString binding.modelVersion ∧
              binding.valuationBefore ≤ binding.valuationAfter)

end AttributionBinding

/-- One locally quadratic factor approximation around the previous valuation
    point. `halfSecondSensitivity` already contains the one-half Taylor factor,
    so all controlled arithmetic remains exact over integer registered units. -/
structure LocalQuadraticAttribution where
  factorId : String
  baseValue : Int
  firstSensitivity : Int
  halfSecondSensitivity : Int
  marketMove : Int
  claimedFirstOrderPnl : Int
  claimedSecondOrderPnl : Int
  availableAt : Timestamp
  binding : AttributionBinding
  deriving Repr, DecidableEq

namespace LocalQuadraticAttribution

def firstOrderPnl (factor : LocalQuadraticAttribution) : Int :=
  factor.firstSensitivity * factor.marketMove

def secondOrderPnl (factor : LocalQuadraticAttribution) : Int :=
  factor.halfSecondSensitivity * factor.marketMove * factor.marketMove

def explainedPnl (factor : LocalQuadraticAttribution) : Int :=
  factor.firstOrderPnl + factor.secondOrderPnl

def claimedExplainedPnl (factor : LocalQuadraticAttribution) : Int :=
  factor.claimedFirstOrderPnl + factor.claimedSecondOrderPnl

def modeledAfterValue (factor : LocalQuadraticAttribution) : Int :=
  factor.baseValue + factor.explainedPnl

/-- Exact closure of the declared local quadratic model. This theorem does not
    claim that a real price function is quadratic; it proves the arithmetic of
    the registered approximation. -/
theorem exact_local_quadratic_closure
    (factor : LocalQuadraticAttribution) :
    factor.modeledAfterValue - factor.baseValue = factor.explainedPnl := by
  simp [modeledAfterValue]

/-- The implementation-reported first- and second-order terms match the exact
    registered local quadratic expression. -/
def FormulaValid (factor : LocalQuadraticAttribution) : Bool :=
  decide (
    factor.claimedFirstOrderPnl = factor.firstOrderPnl ∧
      factor.claimedSecondOrderPnl = factor.secondOrderPnl)

/-- The attribution and its market inputs existed by the decision boundary. -/
def AvailableBy
    (factor : LocalQuadraticAttribution)
    (decisionAt : Timestamp) : Bool :=
  decide (
    factor.availableAt ≤ decisionAt ∧
      factor.binding.valuationBefore ≤ factor.binding.valuationAfter ∧
        factor.binding.valuationAfter ≤ decisionAt)

/-- The local attribution refers to the exact global pipeline identity. -/
def BoundTo
    (factor : LocalQuadraticAttribution)
    (binding : AttributionBinding) : Bool :=
  decide (factor.binding = binding)

end LocalQuadraticAttribution

/-- PnL components not represented by the selected market-risk Taylor basis. -/
structure NonMarketPnl where
  carry : Int
  trades : Int
  cashflows : Int
  transactionCost : Int
  modelRevision : Int
  deriving Repr, DecidableEq

namespace NonMarketPnl

def total (components : NonMarketPnl) : Int :=
  components.carry + components.trades + components.cashflows -
    components.transactionCost + components.modelRevision

end NonMarketPnl

/-- Realized result and the identity of the pipeline that produced it. -/
structure RealizedPnlResult where
  realizedPnl : Int
  generatedAt : Timestamp
  binding : AttributionBinding
  deriving Repr, DecidableEq

/-- Complete bounded PnL-explain application. -/
structure PnlExplain where
  explanationId : String
  decisionAt : Timestamp
  tolerance : Nat
  binding : AttributionBinding
  factors : List LocalQuadraticAttribution
  nonMarket : NonMarketPnl
  result : RealizedPnlResult
  deriving Repr, DecidableEq

namespace PnlExplain

def marketExplainedPnl (explain : PnlExplain) : Int :=
  explain.factors.foldl
    (fun total factor => total + factor.claimedExplainedPnl) 0

def reconstructedPnl (explain : PnlExplain) : Int :=
  explain.marketExplainedPnl + explain.nonMarket.total

def residual (explain : PnlExplain) : Int :=
  explain.result.realizedPnl - explain.reconstructedPnl

def formulasValid (explain : PnlExplain) : Bool :=
  explain.factors.all LocalQuadraticAttribution.FormulaValid

def factorsAvailable (explain : PnlExplain) : Bool :=
  explain.factors.all
    (fun factor => factor.AvailableBy explain.decisionAt)

def factorsBound (explain : PnlExplain) : Bool :=
  explain.factors.all
    (fun factor => factor.BoundTo explain.binding)

def resultBound (explain : PnlExplain) : Bool :=
  decide (
    explain.result.binding = explain.binding ∧
      explain.result.generatedAt ≤ explain.decisionAt)

def bindingWellFormed (explain : PnlExplain) : Bool :=
  explain.binding.WellFormed

def residualWithinTolerance (explain : PnlExplain) : Bool :=
  decide (explain.residual.natAbs ≤ explain.tolerance)

/-- All local arithmetic, temporal, and cross-object obligations except the
    residual-size test. -/
def LocalAndBindingValid (explain : PnlExplain) : Prop :=
  explain.formulasValid = true ∧
    explain.factorsAvailable = true ∧
      explain.factorsBound = true ∧
        explain.resultBound = true ∧
          explain.bindingWellFormed = true

/-- CLOSED means the explanation is correctly bound and its unexplained
    residual lies within the preregistered tolerance. -/
def Closed (explain : PnlExplain) : Prop :=
  explain.LocalAndBindingValid ∧
    explain.residualWithinTolerance = true

/-- PARTIAL means the arithmetic and binding are valid but the residual is
    material relative to the registered tolerance. -/
def Partial (explain : PnlExplain) : Prop :=
  explain.LocalAndBindingValid ∧
    explain.residualWithinTolerance = false

/-- OPEN means at least one formula, time, identity, or result-binding
    obligation failed. -/
def Open (explain : PnlExplain) : Prop :=
  ¬ explain.LocalAndBindingValid

end PnlExplain

/-- Proof-carrying CLOSED explanation. -/
structure PnlExplainClosureCertificate where
  explain : PnlExplain
  closed : explain.Closed

namespace PnlExplainClosureCertificate

theorem local_formulas_are_valid
    (certificate : PnlExplainClosureCertificate) :
    certificate.explain.formulasValid = true :=
  certificate.closed.1.1

theorem all_attributions_share_one_pipeline
    (certificate : PnlExplainClosureCertificate) :
    certificate.explain.factorsBound = true :=
  certificate.closed.1.2.2.1

theorem realized_result_is_bound
    (certificate : PnlExplainClosureCertificate) :
    certificate.explain.resultBound = true :=
  certificate.closed.1.2.2.2.1

theorem residual_is_within_registered_tolerance
    (certificate : PnlExplainClosureCertificate) :
    certificate.explain.residual.natAbs ≤ certificate.explain.tolerance := by
  have passed := certificate.closed.2
  simpa [PnlExplain.residualWithinTolerance] using passed

end PnlExplainClosureCertificate

end LeanFinance.PnL
