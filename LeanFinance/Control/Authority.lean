namespace LeanFinance.Control

/-- Monotone autonomy ladder plus emergency states. `fallback` and `revoked` are
    not promotion targets. -/
inductive AuthorityLevel where
  | observe
  | shadow
  | recommend
  | microAutonomy
  | boundedAutonomy
  | fallback
  | revoked
  deriving Repr, DecidableEq

namespace AuthorityLevel

def next : AuthorityLevel → AuthorityLevel
  | .observe => .shadow
  | .shadow => .recommend
  | .recommend => .microAutonomy
  | .microAutonomy => .boundedAutonomy
  | .boundedAutonomy => .boundedAutonomy
  | .fallback => .fallback
  | .revoked => .revoked

/-- Example registered capital caps. Production values remain governance inputs. -/
def capitalCap : AuthorityLevel → Nat
  | .observe | .shadow | .recommend | .fallback | .revoked => 0
  | .microAutonomy => 10
  | .boundedAutonomy => 100

theorem revoked_has_zero_cap : capitalCap .revoked = 0 := rfl

theorem recommend_has_zero_cap : capitalCap .recommend = 0 := rfl

end AuthorityLevel

/-- Evidence supplied to the autonomy governor. The confidence-sequence and OPE
    construction behind these numbers is added by the statistics layer; this
    module enforces the registered gate. -/
structure PromotionEvidence where
  improvementLcb : Int
  effectiveSampleSize : Nat
  minimumEffectiveSampleSize : Nat
  riskUcb : Nat
  riskBudget : Nat
  modelShift : Bool
  operationalBreach : Bool
  deriving Repr, DecidableEq

namespace PromotionEvidence

def eligible (evidence : PromotionEvidence) : Bool :=
  decide (0 < evidence.improvementLcb) &&
    decide (evidence.minimumEffectiveSampleSize ≤
      evidence.effectiveSampleSize) &&
    decide (evidence.riskUcb ≤ evidence.riskBudget)

end PromotionEvidence

/-- Anytime authority governor. Safety or model-shift violations revoke; a fully
    eligible certificate advances exactly one level; otherwise authority is
    unchanged. -/
def governAuthority
    (current : AuthorityLevel)
    (evidence : PromotionEvidence) : AuthorityLevel :=
  if evidence.modelShift || evidence.operationalBreach then
    .revoked
  else if evidence.eligible then
    current.next
  else
    current

/-- Any operational breach forces immediate revocation. -/
theorem operational_breach_forces_revocation
    (current : AuthorityLevel)
    (evidence : PromotionEvidence)
    (breach : evidence.operationalBreach = true) :
    governAuthority current evidence = .revoked := by
  simp [governAuthority, breach]

/-- A detected model shift also forces immediate revocation. -/
theorem model_shift_forces_revocation
    (current : AuthorityLevel)
    (evidence : PromotionEvidence)
    (shift : evidence.modelShift = true) :
    governAuthority current evidence = .revoked := by
  simp [governAuthority, shift]

end LeanFinance.Control
