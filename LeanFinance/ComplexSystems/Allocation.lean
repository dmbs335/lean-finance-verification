import LeanFinance.ComplexSystems.State

namespace LeanFinance.ComplexSystems

/-- Allocation units are percentage points. The policy keeps a 70% strategic
    core and permits at most a 30% tactical overlay. -/
def coreRiskUnits : Nat := 70

def tacticalBudgetUnits : Nat := 30

/-- Tactical risk budget before the volatility cap. More fragile or weaker-trend
    states never receive a larger overlay. -/
def tacticalOverlayUnits : TrendState → FragilityState → Nat
  | .strong, .low => 30
  | .strong, .elevated => 24
  | .strong, .high => 15
  | .mixed, .low => 15
  | .mixed, .elevated => 10
  | .mixed, .high => 5
  | .weak, _ => 0

/-- Volatility is used as a portfolio-risk cap rather than a directional signal. -/
def volatilityCapUnits : VolatilityState → Nat
  | .normal => 100
  | .stressed => 85

def unconstrainedTargetRiskUnits (state : MarketState) : Nat :=
  coreRiskUnits + tacticalOverlayUnits state.trend state.fragility

/-- Final risky-asset target. `Nat.min` makes the volatility overlay a cap and
    prevents it from increasing exposure. -/
def targetRiskUnits (state : MarketState) : Nat :=
  Nat.min (unconstrainedTargetRiskUnits state)
    (volatilityCapUnits state.volatility)

def safeAssetUnits (state : MarketState) : Nat :=
  100 - targetRiskUnits state

/-- The strategic core is never liquidated by the tactical policy. -/
theorem targetRiskUnits_core_floor (state : MarketState) :
    coreRiskUnits ≤ targetRiskUnits state := by
  cases state with
  | mk trend fragility volatility =>
      cases trend <;> cases fragility <;> cases volatility <;> decide

/-- The policy never recommends leverage above the 100-unit budget. -/
theorem targetRiskUnits_at_most_full (state : MarketState) :
    targetRiskUnits state ≤ 100 := by
  cases state with
  | mk trend fragility volatility =>
      cases trend <;> cases fragility <;> cases volatility <;> decide

theorem targetRiskUnits_positive (state : MarketState) :
    0 < targetRiskUnits state := by
  cases state with
  | mk trend fragility volatility =>
      cases trend <;> cases fragility <;> cases volatility <;> decide

/-- Risk and safe-asset allocations exhaust the 100-unit budget exactly. -/
theorem safe_and_risk_sum_to_full (state : MarketState) :
    safeAssetUnits state + targetRiskUnits state = 100 := by
  cases state with
  | mk trend fragility volatility =>
      cases trend <;> cases fragility <;> cases volatility <;> decide

theorem tactical_overlay_respects_budget (state : MarketState) :
    targetRiskUnits state - coreRiskUnits ≤ tacticalBudgetUnits := by
  cases state with
  | mk trend fragility volatility =>
      cases trend <;> cases fragility <;> cases volatility <;> decide

/-- Moving from low to elevated fragility cannot increase risky allocation. -/
theorem elevated_fragility_not_more_than_low
    (trend : TrendState)
    (volatility : VolatilityState) :
    targetRiskUnits ⟨trend, .elevated, volatility⟩ ≤
      targetRiskUnits ⟨trend, .low, volatility⟩ := by
  cases trend <;> cases volatility <;> decide

/-- Moving from elevated to high fragility cannot increase risky allocation. -/
theorem high_fragility_not_more_than_elevated
    (trend : TrendState)
    (volatility : VolatilityState) :
    targetRiskUnits ⟨trend, .high, volatility⟩ ≤
      targetRiskUnits ⟨trend, .elevated, volatility⟩ := by
  cases trend <;> cases volatility <;> decide

/-- A mixed trend never receives more risk than a strong trend under the same
    fragility and volatility state. -/
theorem mixed_trend_not_more_than_strong
    (fragility : FragilityState)
    (volatility : VolatilityState) :
    targetRiskUnits ⟨.mixed, fragility, volatility⟩ ≤
      targetRiskUnits ⟨.strong, fragility, volatility⟩ := by
  cases fragility <;> cases volatility <;> decide

/-- A weak trend never receives more risk than a mixed trend. -/
theorem weak_trend_not_more_than_mixed
    (fragility : FragilityState)
    (volatility : VolatilityState) :
    targetRiskUnits ⟨.weak, fragility, volatility⟩ ≤
      targetRiskUnits ⟨.mixed, fragility, volatility⟩ := by
  cases fragility <;> cases volatility <;> decide

/-- A volatility-stress flag can only reduce or preserve the target. -/
theorem volatility_stress_not_more_than_normal
    (trend : TrendState)
    (fragility : FragilityState) :
    targetRiskUnits ⟨trend, fragility, .stressed⟩ ≤
      targetRiskUnits ⟨trend, fragility, .normal⟩ := by
  cases trend <;> cases fragility <;> decide

/-- Weak trend removes the tactical overlay but preserves the strategic core. -/
theorem weak_trend_is_core_only
    (fragility : FragilityState)
    (volatility : VolatilityState) :
    targetRiskUnits ⟨.weak, fragility, volatility⟩ = coreRiskUnits := by
  cases fragility <;> cases volatility <;> decide

theorem strong_low_normal_is_fully_allocated :
    targetRiskUnits ⟨.strong, .low, .normal⟩ = 100 := by
  decide

inductive RebalanceAction where
  | buy
  | hold
  | sell
  deriving Repr, DecidableEq

/-- Buy below the target, sell above it, and otherwise hold. -/
def rebalanceAction
    (currentRiskUnits : Nat)
    (state : MarketState) : RebalanceAction :=
  if currentRiskUnits < targetRiskUnits state then
    .buy
  else if targetRiskUnits state < currentRiskUnits then
    .sell
  else
    .hold

theorem buy_when_below_target
    (currentRiskUnits : Nat)
    (state : MarketState)
    (below : currentRiskUnits < targetRiskUnits state) :
    rebalanceAction currentRiskUnits state = .buy := by
  simp [rebalanceAction, below]

theorem sell_when_above_target
    (currentRiskUnits : Nat)
    (state : MarketState)
    (above : targetRiskUnits state < currentRiskUnits) :
    rebalanceAction currentRiskUnits state = .sell := by
  have notBelow : ¬ currentRiskUnits < targetRiskUnits state :=
    Nat.lt_asymm above
  simp [rebalanceAction, notBelow, above]

theorem hold_when_at_target
    (state : MarketState) :
    rebalanceAction (targetRiskUnits state) state = .hold := by
  simp [rebalanceAction]

theorem rebalanceAction_buy_sound
    (currentRiskUnits : Nat)
    (state : MarketState)
    (actionIsBuy :
      rebalanceAction currentRiskUnits state = .buy) :
    currentRiskUnits < targetRiskUnits state := by
  by_cases below : currentRiskUnits < targetRiskUnits state
  · exact below
  · by_cases above : targetRiskUnits state < currentRiskUnits
    · simp [rebalanceAction, below, above] at actionIsBuy
    · simp [rebalanceAction, below, above] at actionIsBuy

theorem rebalanceAction_sell_sound
    (currentRiskUnits : Nat)
    (state : MarketState)
    (actionIsSell :
      rebalanceAction currentRiskUnits state = .sell) :
    targetRiskUnits state < currentRiskUnits := by
  by_cases below : currentRiskUnits < targetRiskUnits state
  · simp [rebalanceAction, below] at actionIsSell
  · by_cases above : targetRiskUnits state < currentRiskUnits
    · exact above
    · simp [rebalanceAction, below, above] at actionIsSell

end LeanFinance.ComplexSystems
