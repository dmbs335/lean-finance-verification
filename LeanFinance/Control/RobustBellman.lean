namespace LeanFinance.Control

/-- One weighted continuation value in a finite Bellman backup. -/
structure WeightedContinuation where
  weight : Nat
  value : Int
  deriving Repr, DecidableEq

def totalContinuationWeight
    (branches : List WeightedContinuation) : Nat :=
  branches.foldl (fun total branch => total + branch.weight) 0

def weightedContinuationNumerator
    (branches : List WeightedContinuation) : Int :=
  branches.foldl
    (fun total branch =>
      total + Int.ofNat branch.weight * branch.value) 0

/-- Cross-multiplied rational Bellman backup.

    Its represented value is

    `reward + discountNumerator / discountDenominator × weighted mean(next)`.

    Integer lower bounds can therefore be checked without trusting floating-point
    arithmetic. -/
structure BellmanBackup where
  reward : Int
  discountNumerator : Nat
  discountDenominator : Nat
  continuation : List WeightedContinuation
  deriving Repr, DecidableEq

namespace BellmanBackup

def denominator (backup : BellmanBackup) : Nat :=
  totalContinuationWeight backup.continuation *
    backup.discountDenominator

def numerator (backup : BellmanBackup) : Int :=
  backup.reward * Int.ofNat backup.denominator +
    Int.ofNat backup.discountNumerator *
      weightedContinuationNumerator backup.continuation

def Valid (backup : BellmanBackup) : Prop :=
  0 < backup.discountDenominator ∧
    0 < totalContinuationWeight backup.continuation

/-- `lower` is a sound integer lower bound on the rational backup. -/
def LowerBound (backup : BellmanBackup) (lower : Int) : Prop :=
  Int.ofNat backup.denominator * lower ≤ backup.numerator

theorem lower_bound_is_cross_multiplied
    (backup : BellmanBackup)
    (lower : Int)
    (sound : backup.LowerBound lower) :
    Int.ofNat backup.denominator * lower ≤ backup.numerator :=
  sound

end BellmanBackup

/-- One lower bound must hold under every model still admitted by evidence. -/
def RobustBellmanLowerBound
    (models : List Model)
    (backup : Model → BellmanBackup)
    (lower : Int) : Prop :=
  ∀ model,
    model ∈ models →
      (backup model).LowerBound lower

/-- Removing models preserves every previously sound robust Bellman lower
    bound. This is the dynamic-programming counterpart of ambiguity refinement. -/
theorem robust_bellman_lower_survives_model_refinement
    (outer inner : List Model)
    (backup : Model → BellmanBackup)
    (lower : Int)
    (refines : ∀ model, model ∈ inner → model ∈ outer)
    (sound : RobustBellmanLowerBound outer backup lower) :
    RobustBellmanLowerBound inner backup lower := by
  intro model member
  exact sound model (refines model member)

/-- Proof-carrying model-wise backup for one action. -/
structure RobustBellmanActionCertificate (Model : Type) where
  models : List Model
  lowerBound : Int
  backup : Model → BellmanBackup
  valid :
    ∀ model,
      model ∈ models →
        (backup model).Valid
  sound : RobustBellmanLowerBound models backup lowerBound

/-- A state certificate selects one action and proves that its robust lower bound
    dominates all declared alternative lower bounds. -/
structure RobustBellmanStateCertificate (Model Action : Type) where
  selectedAction : Action
  selected : RobustBellmanActionCertificate Model
  declaredActionLower : Action → Int
  selectedMatches :
    declaredActionLower selectedAction = selected.lowerBound
  selectedDominates :
    ∀ action,
      declaredActionLower action ≤ selected.lowerBound

namespace RobustBellmanStateCertificate

theorem selected_lower_holds_for_every_model
    (certificate : RobustBellmanStateCertificate Model Action)
    (model : Model)
    (member : model ∈ certificate.selected.models) :
    (certificate.selected.backup model).LowerBound
      certificate.selected.lowerBound :=
  certificate.selected.sound model member

theorem selected_dominates_every_declared_action
    (certificate : RobustBellmanStateCertificate Model Action)
    (action : Action) :
    certificate.declaredActionLower action ≤
      certificate.selected.lowerBound :=
  certificate.selectedDominates action

end RobustBellmanStateCertificate

end LeanFinance.Control
