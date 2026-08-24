import LeanFinance.Alpha.Certifiable

namespace LeanFinance.Alpha

/-- Structural response parameters linking evidence confidence to capital and
    capital to crowding cost. All quantities are nonnegative integers in the
    bounded theorem; empirical calibration is outside the formal claim. -/
structure CrowdingResponse where
  allocatorScale : Nat
  impactCoefficient : Nat
  deriving Repr

def allocatedCapital
    (response : CrowdingResponse)
    (evidenceConfidence : Nat) : Nat :=
  response.allocatorScale * evidenceConfidence

def crowdingCost
    (response : CrowdingResponse)
    (evidenceConfidence : Nat) : Nat :=
  response.impactCoefficient *
    allocatedCapital response evidenceConfidence

def deployableAlpha
    (economicAlpha : RealizedAlpha)
    (response : CrowdingResponse)
    (evidenceConfidence : Nat) : RealizedAlpha :=
  economicAlpha - Int.ofNat (crowdingCost response evidenceConfidence)

/-- Stronger allocator confidence weakly increases allocated capital under a
    fixed nonnegative response. -/
theorem higher_certifiability_increases_allocation
    (response : CrowdingResponse)
    (weak strong : Nat)
    (higherConfidence : weak ≤ strong) :
    allocatedCapital response weak ≤
      allocatedCapital response strong := by
  exact Nat.mul_le_mul_left response.allocatorScale higherConfidence

/-- The certifiability-crowding law in its structural form: if greater evidence
    confidence attracts more capital and price impact is nonnegative, the same
    economic alpha has weakly lower deployable alpha after crowding. This is not
    a claim that the response is empirically large or universally present. -/
theorem higher_certifiability_can_reduce_deployable_alpha
    (economicAlpha : RealizedAlpha)
    (response : CrowdingResponse)
    (weak strong : Nat)
    (higherConfidence : weak ≤ strong) :
    deployableAlpha economicAlpha response strong ≤
      deployableAlpha economicAlpha response weak := by
  have allocationMonotone :
      allocatedCapital response weak ≤
        allocatedCapital response strong :=
    higher_certifiability_increases_allocation
      response weak strong higherConfidence
  have costMonotone :
      crowdingCost response weak ≤ crowdingCost response strong := by
    exact Nat.mul_le_mul_left response.impactCoefficient
      allocationMonotone
  exact Int.sub_le_sub_left (Int.ofNat_le.2 costMonotone) economicAlpha

/-- With zero market impact, stronger evidence can change allocation without
    changing deployable alpha. -/
theorem zero_impact_preserves_deployable_alpha
    (economicAlpha : RealizedAlpha)
    (allocatorScale weak strong : Nat) :
    deployableAlpha economicAlpha
        { allocatorScale := allocatorScale, impactCoefficient := 0 }
        strong =
      deployableAlpha economicAlpha
        { allocatorScale := allocatorScale, impactCoefficient := 0 }
        weak := by
  simp [deployableAlpha, crowdingCost]

end LeanFinance.Alpha
