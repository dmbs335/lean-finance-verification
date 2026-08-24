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

/-- Three distinct reasons that an apparent alpha can cease to be investable. -/
inductive AlphaDeathMode where
  | epistemic
  | capacity
  | ecological
  deriving Repr, DecidableEq

/-- Epistemic death: the evidence-supported lower bound is nonpositive, so the
    research process does not defend a positive edge. -/
def EpistemicDeath (certifiableLower : RealizedAlpha) : Prop :=
  certifiableLower ≤ 0

/-- Capacity death: gross economic alpha remains positive but modeled crowding
    cost consumes the complete deployable edge. -/
def CapacityDeath
    (economicAlpha : RealizedAlpha)
    (response : CrowdingResponse)
    (evidenceConfidence : Nat) : Prop :=
  0 < economicAlpha ∧
    deployableAlpha economicAlpha response evidenceConfidence ≤ 0

/-- Ecological decay: the gross economic edge itself falls after market
    participants adapt. This is separate from process validity and capacity. -/
def EcologicalDecay
    (economicAlphaBefore economicAlphaAfter : RealizedAlpha) : Prop :=
  economicAlphaAfter < economicAlphaBefore

/-- A proof-carrying witness that a strategy crosses from positive deployable
    alpha to capacity death as confidence-driven allocation rises. -/
structure CapacityExtinctionWitness where
  economicAlpha : RealizedAlpha
  response : CrowdingResponse
  weakConfidence : Nat
  strongConfidence : Nat
  higherConfidence : weakConfidence ≤ strongConfidence
  economicAlphaPositive : 0 < economicAlpha
  beforeInvestable :
    0 < deployableAlpha economicAlpha response weakConfidence
  afterNonpositive :
    deployableAlpha economicAlpha response strongConfidence ≤ 0

namespace CapacityExtinctionWitness

theorem after_is_capacity_dead
    (witness : CapacityExtinctionWitness) :
    CapacityDeath witness.economicAlpha witness.response
      witness.strongConfidence :=
  ⟨witness.economicAlphaPositive, witness.afterNonpositive⟩

theorem deployable_alpha_weakly_falls
    (witness : CapacityExtinctionWitness) :
    deployableAlpha witness.economicAlpha witness.response
        witness.strongConfidence ≤
      deployableAlpha witness.economicAlpha witness.response
        witness.weakConfidence :=
  higher_certifiability_can_reduce_deployable_alpha
    witness.economicAlpha witness.response
    witness.weakConfidence witness.strongConfidence
    witness.higherConfidence

end CapacityExtinctionWitness

/-- A strategy can be capacity-dead while its certifiable lower bound remains
    positive; epistemic and capacity death are logically distinct. -/
theorem capacity_death_does_not_imply_epistemic_death
    (certifiableLower economicAlpha : RealizedAlpha)
    (response : CrowdingResponse)
    (evidenceConfidence : Nat)
    (certifiablePositive : 0 < certifiableLower)
    (_capacityDead :
      CapacityDeath economicAlpha response evidenceConfidence) :
    ¬ EpistemicDeath certifiableLower := by
  intro epistemicDead
  exact (Int.not_lt_of_ge epistemicDead) certifiablePositive

end LeanFinance.Alpha
