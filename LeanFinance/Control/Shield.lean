namespace LeanFinance.Control

/-- Trusted runtime safety boundary. The advanced controller supplies a proposal;
    the shield either accepts it or returns a total verified fallback. -/
structure SafetyShield (State Action : Type) where
  admissible : State → Action → Bool
  fallback : State → Action
  fallbackAdmissible :
    ∀ state, admissible state (fallback state) = true

namespace SafetyShield

/-- Apply the advanced proposal only when the trusted admissibility checker
    accepts it. -/
def apply
    (shield : SafetyShield State Action)
    (state : State)
    (proposal : Action) : Action :=
  if shield.admissible state proposal = true then
    proposal
  else
    shield.fallback state

/-- Every shield output is accepted by the same trusted checker. -/
theorem apply_is_admissible
    (shield : SafetyShield State Action)
    (state : State)
    (proposal : Action) :
    shield.admissible state (shield.apply state proposal) = true := by
  unfold apply
  by_cases accepted : shield.admissible state proposal = true
  · simp [accepted]
  · simp [accepted, shield.fallbackAdmissible]

/-- A rejected proposal is replaced by the declared fallback exactly. -/
theorem rejected_proposal_uses_fallback
    (shield : SafetyShield State Action)
    (state : State)
    (proposal : Action)
    (rejected : shield.admissible state proposal ≠ true) :
    shield.apply state proposal = shield.fallback state := by
  simp [apply, rejected]

end SafetyShield

end LeanFinance.Control
