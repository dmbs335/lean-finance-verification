import LeanFinance.StateSpace.Model

namespace LeanFinance.StateSpace

universe u v

/-- An exact finite-dimensional Koopman closure certificate. `IsLinear` is
    supplied by the chosen feature-space theory; Lean separately checks that the
    lift intertwines one state step with one feature-space operator step. -/
structure KoopmanCertificate
    (State : Type u)
    (Feature : Type v)
    (IsLinear : (Feature → Feature) → Prop) where
  stateStep : State → State
  lift : State → Feature
  operator : Feature → Feature
  linear : IsLinear operator
  intertwines :
    ∀ state,
      lift (stateStep state) = operator (lift state)

theorem KoopmanCertificate.intertwines_iterate
    {State : Type u}
    {Feature : Type v}
    {IsLinear : (Feature → Feature) → Prop}
    (certificate :
      KoopmanCertificate State Feature IsLinear)
    (steps : Nat)
    (state : State) :
    certificate.lift
        (iterateStep certificate.stateStep steps state) =
      iterateStep certificate.operator steps
        (certificate.lift state) := by
  induction steps with
  | zero =>
      rfl
  | succ steps inductionHypothesis =>
      calc
        certificate.lift
            (iterateStep certificate.stateStep
              (Nat.succ steps) state) =
          certificate.lift
            (certificate.stateStep
              (iterateStep certificate.stateStep
                steps state)) := rfl
        _ = certificate.operator
              (certificate.lift
                (iterateStep certificate.stateStep
                  steps state)) :=
          certificate.intertwines _
        _ = certificate.operator
              (iterateStep certificate.operator steps
                (certificate.lift state)) :=
          congrArg certificate.operator inductionHypothesis
        _ = iterateStep certificate.operator
              (Nat.succ steps)
              (certificate.lift state) := rfl

end LeanFinance.StateSpace
