import LeanFinance.Core

namespace LeanFinance.Allocation

/-- Stable identifier for the deterministic allocation contract. -/
def policyStrategyId : StrategyId :=
  "core-trend-fragility-allocation"

/-- Coarse medium-horizon trend state used by the allocation policy. -/
inductive TrendState where
  | rising
  | mixed
  | falling
  deriving Repr, DecidableEq

/-- Endogenous fragility is kept separate from trend direction. -/
inductive FragilityState where
  | low
  | medium
  | high
  deriving Repr, DecidableEq

/-- Realized-risk state acts as a cap, not as an independent directional signal. -/
inductive VolatilityState where
  | normal
  | elevated
  | stressed
  deriving Repr, DecidableEq

/-- Inputs are deliberately discrete so an empirical adapter must publish the
    exact classification that was available at the decision time. -/
structure PolicyInput where
  trend : TrendState
  fragility : FragilityState
  volatility : VolatilityState
  deriving Repr, DecidableEq

/-- The strategic core is 70% of portfolio capital. -/
def coreRiskBps : Nat := 7000

/-- The tactical sleeve is divided into ten exact 3% steps. -/
def tacticalUnitBps : Nat := 300

/-- Maximum tactical units: ten units represent the full 30% sleeve. -/
def maxTacticalUnits : Nat := 10

/-- Total portfolio exposure is capped at 100%. -/
def fullRiskBps : Nat := 10000

/-- Trend and fragility jointly determine the uncapped tactical allowance.

The table intentionally distinguishes direction from fragility:

* rising / low: 100% of the tactical sleeve;
* rising / medium: 80%;
* rising / high: 70%;
* mixed / low: 50%;
* mixed / medium: 40%;
* mixed / high: 20%;
* falling: no tactical sleeve.
-/
def baseTacticalUnits : TrendState → FragilityState → Nat
  | .rising, .low => 10
  | .rising, .medium => 8
  | .rising, .high => 7
  | .mixed, .low => 5
  | .mixed, .medium => 4
  | .mixed, .high => 2
  | .falling, _ => 0

/-- Volatility only caps the tactical allowance. It never creates exposure. -/
def volatilityCapUnits : VolatilityState → Nat
  | .normal => 10
  | .elevated => 8
  | .stressed => 5

/-- Final tactical exposure is the smaller of the directional/fragility
    allowance and the volatility cap. -/
def targetTacticalUnits
    (trend : TrendState)
    (fragility : FragilityState)
    (volatility : VolatilityState) : Nat :=
  min (baseTacticalUnits trend fragility)
    (volatilityCapUnits volatility)

/-- Portfolio exposure in basis points. The policy never shorts and never
    liquidates the strategic core. -/
def targetRiskBps
    (trend : TrendState)
    (fragility : FragilityState)
    (volatility : VolatilityState) : Nat :=
  coreRiskBps + tacticalUnitBps *
    targetTacticalUnits trend fragility volatility

structure AllocationDecision where
  tacticalUnits : Nat
  riskBps : Nat
  deriving Repr, DecidableEq

/-- Deterministic policy output bound into a certificate. -/
def allocationDecision (input : PolicyInput) : AllocationDecision :=
  {
    tacticalUnits :=
      targetTacticalUnits input.trend input.fragility input.volatility
    riskBps :=
      targetRiskBps input.trend input.fragility input.volatility
  }

/-- Buy and sell are defined relative to the certified target, not from a
    separate crash-timing oracle. -/
inductive RebalanceDirection where
  | buy
  | hold
  | sell
  deriving Repr, DecidableEq

/-- Compare current exposure with the deterministic target. -/
def rebalanceDirection
    (currentRiskBps targetRiskBps : Nat) : RebalanceDirection :=
  if currentRiskBps < targetRiskBps then
    .buy
  else if targetRiskBps < currentRiskBps then
    .sell
  else
    .hold

/-- Compute the direction directly from policy input. -/
def allocationDirection
    (currentRiskBps : Nat)
    (input : PolicyInput) : RebalanceDirection :=
  rebalanceDirection currentRiskBps (allocationDecision input).riskBps

/-- A weakening relation is explicit rather than inferred from constructor order. -/
inductive TrendWeakens : TrendState → TrendState → Prop where
  | risingStays : TrendWeakens .rising .rising
  | risingToMixed : TrendWeakens .rising .mixed
  | risingToFalling : TrendWeakens .rising .falling
  | mixedStays : TrendWeakens .mixed .mixed
  | mixedToFalling : TrendWeakens .mixed .falling
  | fallingStays : TrendWeakens .falling .falling

/-- A worsening fragility relation. -/
inductive FragilityWorsens : FragilityState → FragilityState → Prop where
  | lowStays : FragilityWorsens .low .low
  | lowToMedium : FragilityWorsens .low .medium
  | lowToHigh : FragilityWorsens .low .high
  | mediumStays : FragilityWorsens .medium .medium
  | mediumToHigh : FragilityWorsens .medium .high
  | highStays : FragilityWorsens .high .high

/-- A worsening volatility relation. -/
inductive VolatilityWorsens : VolatilityState → VolatilityState → Prop where
  | normalStays : VolatilityWorsens .normal .normal
  | normalToElevated : VolatilityWorsens .normal .elevated
  | normalToStressed : VolatilityWorsens .normal .stressed
  | elevatedStays : VolatilityWorsens .elevated .elevated
  | elevatedToStressed : VolatilityWorsens .elevated .stressed
  | stressedStays : VolatilityWorsens .stressed .stressed

theorem targetTacticalUnits_le_max
    (trend : TrendState)
    (fragility : FragilityState)
    (volatility : VolatilityState) :
    targetTacticalUnits trend fragility volatility ≤ maxTacticalUnits := by
  cases trend <;> cases fragility <;> cases volatility <;> decide

/-- The policy cannot liquidate the 70% strategic core. -/
theorem core_floor
    (trend : TrendState)
    (fragility : FragilityState)
    (volatility : VolatilityState) :
    coreRiskBps ≤ targetRiskBps trend fragility volatility := by
  cases trend <;> cases fragility <;> cases volatility <;> decide

/-- The policy cannot exceed 100% exposure. -/
theorem full_investment_ceiling
    (trend : TrendState)
    (fragility : FragilityState)
    (volatility : VolatilityState) :
    targetRiskBps trend fragility volatility ≤ fullRiskBps := by
  cases trend <;> cases fragility <;> cases volatility <;> decide

/-- Falling trend removes only the tactical sleeve. -/
theorem falling_has_zero_tactical
    (fragility : FragilityState)
    (volatility : VolatilityState) :
    targetTacticalUnits .falling fragility volatility = 0 := by
  cases fragility <;> cases volatility <;> decide

/-- Falling trend therefore leaves exactly the strategic core. -/
theorem falling_preserves_core
    (fragility : FragilityState)
    (volatility : VolatilityState) :
    targetRiskBps .falling fragility volatility = coreRiskBps := by
  cases fragility <;> cases volatility <;> decide

/-- Weakening trend cannot increase tactical exposure. -/
theorem weakening_trend_never_increases
    {oldTrend newTrend : TrendState}
    (weakens : TrendWeakens oldTrend newTrend)
    (fragility : FragilityState)
    (volatility : VolatilityState) :
    targetTacticalUnits newTrend fragility volatility ≤
      targetTacticalUnits oldTrend fragility volatility := by
  cases weakens <;> cases fragility <;> cases volatility <;> decide

/-- Worsening fragility cannot increase tactical exposure. -/
theorem worsening_fragility_never_increases
    (trend : TrendState)
    {oldFragility newFragility : FragilityState}
    (worsens : FragilityWorsens oldFragility newFragility)
    (volatility : VolatilityState) :
    targetTacticalUnits trend newFragility volatility ≤
      targetTacticalUnits trend oldFragility volatility := by
  cases worsens <;> cases trend <;> cases volatility <;> decide

/-- Worsening volatility cannot increase tactical exposure. -/
theorem worsening_volatility_never_increases
    (trend : TrendState)
    (fragility : FragilityState)
    {oldVolatility newVolatility : VolatilityState}
    (worsens : VolatilityWorsens oldVolatility newVolatility) :
    targetTacticalUnits trend fragility newVolatility ≤
      targetTacticalUnits trend fragility oldVolatility := by
  cases worsens <;> cases trend <;> cases fragility <;> decide

/-- Exposure below target always produces a buy instruction. -/
theorem rebalanceDirection_buy_of_below
    (currentRisk targetRisk : Nat)
    (below : currentRisk < targetRisk) :
    rebalanceDirection currentRisk targetRisk = .buy := by
  simp [rebalanceDirection, below]

/-- Exposure above target always produces a sell instruction. -/
theorem rebalanceDirection_sell_of_above
    (currentRisk targetRisk : Nat)
    (above : targetRisk < currentRisk) :
    rebalanceDirection currentRisk targetRisk = .sell := by
  have notBelow : ¬ currentRisk < targetRisk := by
    intro below
    exact Nat.lt_asymm below above
  simp [rebalanceDirection, notBelow, above]

/-- Exposure exactly at target produces no trade. -/
theorem rebalanceDirection_hold_at_target (targetRisk : Nat) :
    rebalanceDirection targetRisk targetRisk = .hold := by
  simp [rebalanceDirection]

/-- The fully favorable state uses all capital without leverage. -/
theorem favorable_state_is_fully_invested :
    targetRiskBps .rising .low .normal = fullRiskBps := by
  decide

/-- High fragility reduces, but does not reverse, a still-rising trend. -/
theorem rising_high_fragility_target :
    targetRiskBps .rising .high .normal = 9100 := by
  decide

/-- Mixed trend plus high fragility leaves only 6% tactical exposure. -/
theorem mixed_high_fragility_target :
    targetRiskBps .mixed .high .normal = 7600 := by
  decide

end LeanFinance.Allocation
