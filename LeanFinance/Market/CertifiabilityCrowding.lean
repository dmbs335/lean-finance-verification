import LeanFinance.Core

namespace LeanFinance.Market

/-- One point in the lifecycle of a strategy whose research claim has a
    certifiability level, an allocator capital stock, and an execution impact. -/
structure CertifiabilityCrowdingState where
  certifiability : Scalar
  allocatedCapital : Scalar
  economicAlphaBps : Scalar
  impactBps : Scalar
  deriving Repr

/-- Net alpha remaining after the modeled market-impact burden. -/
def deployableAlphaBps
    (state : CertifiabilityCrowdingState) : Scalar :=
  state.economicAlphaBps - state.impactBps

/-- A transition representing the hypothesized chain from stronger evidence to
    larger allocations and greater crowding impact. The gross economic alpha is
    held fixed so the theorem isolates the crowding channel. -/
structure CertifiabilityCrowdingTransition where
  before : CertifiabilityCrowdingState
  after : CertifiabilityCrowdingState
  certifiabilityIncreased :
    before.certifiability < after.certifiability
  allocationIncreased :
    before.allocatedCapital < after.allocatedCapital
  impactIncreased :
    before.impactBps < after.impactBps
  economicAlphaPreserved :
    before.economicAlphaBps = after.economicAlphaBps

/-- Under the stated allocator and impact response assumptions, stronger
    certifiability can reduce deployable alpha even though gross economic alpha
    has not changed. This is a conditional mechanism, not an empirical law. -/
theorem increased_certifiability_can_reduce_deployable_alpha
    (transition : CertifiabilityCrowdingTransition) :
    deployableAlphaBps transition.after <
      deployableAlphaBps transition.before := by
  unfold deployableAlphaBps
  rw [← transition.economicAlphaPreserved]
  exact sub_lt_sub_left transition.impactIncreased _

/-- A strategy remains investable when its deployable alpha is positive. -/
def Investable
    (state : CertifiabilityCrowdingState) : Prop :=
  0 < deployableAlphaBps state

/-- Capacity death: gross economic alpha remains positive, but modeled impact
    consumes the complete edge. -/
def CapacityDeath
    (state : CertifiabilityCrowdingState) : Prop :=
  0 < state.economicAlphaBps ∧
    deployableAlphaBps state ≤ 0

/-- Epistemic death: the reported strategy may still show a return, but the
    research-integrity claim is not sufficiently certified. -/
def EpistemicDeath
    (state : CertifiabilityCrowdingState) : Prop :=
  state.certifiability ≤ 0

/-- Ecological pressure is represented separately from epistemic validity: a
    strategy can be certified and economically positive while no longer being
    deployable at the current allocation. -/
theorem capacity_death_does_not_imply_epistemic_death
    (state : CertifiabilityCrowdingState)
    (certified : 0 < state.certifiability)
    (capacityDead : CapacityDeath state) :
    ¬ EpistemicDeath state := by
  intro epistemicDead
  exact Int.not_lt_of_ge epistemicDead certified

/-- A before/after pair can cross the investability boundary solely because of
    the impact response to capital. -/
structure CrowdingExtinctionWitness where
  transition : CertifiabilityCrowdingTransition
  beforeInvestable : Investable transition.before
  afterCapacityDead : CapacityDeath transition.after

namespace CrowdingExtinctionWitness

theorem certifiability_success_can_destroy_deployability
    (witness : CrowdingExtinctionWitness) :
    Investable witness.transition.before ∧
      CapacityDeath witness.transition.after :=
  ⟨witness.beforeInvestable, witness.afterCapacityDead⟩

end CrowdingExtinctionWitness

end LeanFinance.Market
