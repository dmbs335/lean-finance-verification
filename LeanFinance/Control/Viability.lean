import LeanFinance.Control.FiniteMDP

namespace LeanFinance.Control

/-- Finite-horizon viability kernel as a predicate. At horizon zero the state
    itself must be safe. At a positive horizon there must be an action whose
    every represented successor remains viable. -/
def ViableAt
    (model : FiniteMDP State Action)
    (safe : State → Prop) : Nat → State → Prop
  | 0, state => safe state
  | horizon + 1, state =>
      safe state ∧
        ∃ action,
          ∀ outcome,
            outcome ∈ model.outcomes state action →
              ViableAt model safe horizon outcome.nextState

/-- Positive-horizon viability includes current-state safety. -/
theorem viableAt_succ_is_safe
    (model : FiniteMDP State Action)
    (safe : State → Prop)
    (horizon : Nat)
    (state : State)
    (viable : ViableAt model safe (horizon + 1) state) :
    safe state := by
  change safe state ∧ _ at viable
  exact viable.1

/-- A viable state carries at least one action preserving the shorter-horizon
    kernel for every represented successor. -/
theorem viableAt_succ_has_preserving_action
    (model : FiniteMDP State Action)
    (safe : State → Prop)
    (horizon : Nat)
    (state : State)
    (viable : ViableAt model safe (horizon + 1) state) :
    ∃ action,
      ∀ outcome,
        outcome ∈ model.outcomes state action →
          ViableAt model safe horizon outcome.nextState := by
  change safe state ∧ _ at viable
  exact viable.2

end LeanFinance.Control
