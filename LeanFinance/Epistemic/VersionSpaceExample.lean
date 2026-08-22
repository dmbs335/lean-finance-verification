import LeanFinance.Epistemic.VersionSpace

namespace LeanFinance.Epistemic.VersionSpaceExample

inductive Semantics where
  | narrow
  | permissive
  deriving Repr, DecidableEq

inductive ObservedTrace where
  | costModelMutation
  deriving Repr, DecidableEq

/-- Both semantics replay the single observed trace. The trace does not reveal
    whether an unobserved control-plane mutation is possible in other states. -/
def consistent : Semantics → ObservedTrace → Prop
  | _, _ => True

def observed : List ObservedTrace := [.costModelMutation]

inductive World where
  | narrowHonest
  | narrowVisibleAttack
  | permissiveHonest
  | permissiveVisibleAttack
  | permissiveSilentMutation
  deriving Repr, DecidableEq

def worldModel : World → Semantics
  | .narrowHonest => .narrow
  | .narrowVisibleAttack => .narrow
  | .permissiveHonest => .permissive
  | .permissiveVisibleAttack => .permissive
  | .permissiveSilentMutation => .permissive

def allowed (world : World) : Prop :=
  VersionSpaceWorld consistent observed worldModel world

def claim : World → Prop
  | .narrowHonest => True
  | .narrowVisibleAttack => False
  | .permissiveHonest => True
  | .permissiveVisibleAttack => False
  | .permissiveSilentMutation => False

inductive Channel where
  | publication
  | mutationReceipt
  deriving Repr, DecidableEq

inductive Observation where
  | clean
  | flagged
  | absent
  | present
  deriving Repr, DecidableEq

def observe : Channel → World → Observation
  | .publication, .narrowHonest => .clean
  | .publication, .narrowVisibleAttack => .flagged
  | .publication, .permissiveHonest => .clean
  | .publication, .permissiveVisibleAttack => .flagged
  | .publication, .permissiveSilentMutation => .clean
  | .mutationReceipt, .narrowHonest => .absent
  | .mutationReceipt, .narrowVisibleAttack => .absent
  | .mutationReceipt, .permissiveHonest => .absent
  | .mutationReceipt, .permissiveVisibleAttack => .absent
  | .mutationReceipt, .permissiveSilentMutation => .present

def publicationOnly (channel : Channel) : Prop :=
  channel = .publication

def familyBasis (channel : Channel) : Prop :=
  channel = .publication ∨ channel = .mutationReceipt

theorem publication_verifies_narrow_point :
    PointModelVerifies worldModel .narrow
      (observe .publication) claim allowed := by
  intro left right _leftAllowed _rightAllowed leftModel rightModel sameEvidence
  cases left <;> cases right <;>
    simp_all [worldModel, claim, observe]

def silentCrossModelCounterexample :
    ModelFamilyCounterexample worldModel
      (observe .publication) claim allowed :=
  {
    left := .narrowHonest
    right := .permissiveSilentMutation
    leftAllowed := by simp [allowed, VersionSpaceWorld, VersionSpace, observed, consistent]
    rightAllowed := by simp [allowed, VersionSpaceWorld, VersionSpace, observed, consistent]
    sameEvidence := rfl
    leftClaim := True.intro
    rightNotClaim := by simp [claim]
    semanticsDiffer := by decide
  }

def pointUnderestimation :
    PointUnderestimationWitness worldModel
      (observe .publication) claim allowed :=
  {
    chosen := .narrow
    pointVerified := publication_verifies_narrow_point
    familyCounterexample := silentCrossModelCounterexample
  }

theorem one_refined_model_underestimates_evidence :
    PointModelVerifies worldModel .narrow
        (observe .publication) claim allowed ∧
      ¬ ModelFamilyVerifies
        (observe .publication) claim allowed :=
  pointUnderestimation.point_refinement_can_underestimate_evidence

theorem publication_plus_receipt_verifies_version_space :
    ModelFamilyChannelSelectionVerifies
      observe familyBasis claim allowed := by
  intro left right _leftAllowed _rightAllowed sameEvidence
  cases left <;> cases right <;>
    simp_all [ChannelsAgree, familyBasis, claim, observe]

/-- The second trace can exclude the permissive semantics, demonstrating the
    antitone version-space law. -/
inductive RefutingTrace where
  | positive
  | negative
  deriving Repr, DecidableEq

def refinedConsistent : Semantics → RefutingTrace → Prop
  | .narrow, _ => True
  | .permissive, .positive => True
  | .permissive, .negative => False

def oldTraces : List RefutingTrace := [.positive]
def newTraces : List RefutingTrace := [.positive, .negative]

theorem narrow_survives_new_trace :
    VersionSpace refinedConsistent newTraces .narrow := by
  intro trace member
  cases trace <;> simp [refinedConsistent]

theorem permissive_excluded_by_new_trace :
    ¬ VersionSpace refinedConsistent newTraces .permissive := by
  intro survives
  have := survives .negative (by simp [newTraces])
  simpa [refinedConsistent] using this

end LeanFinance.Epistemic.VersionSpaceExample
