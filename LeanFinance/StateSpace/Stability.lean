import LeanFinance.StateSpace.Model

namespace LeanFinance.StateSpace

universe u

/-- A local finite-state stability contract. The domain is required to be
    forward invariant, and perturbations may not expand while both states remain
    in that domain. No metric or differentiability claim is inferred. -/
structure LocalStabilityCertificate (State : Type u) where
  step : State → State
  perturbation : State → State → Nat
  domain : State → Prop
  forwardInvariant :
    ∀ state, domain state → domain (step state)
  nonexpansive :
    ∀ left right,
      domain left →
      domain right →
      perturbation (step left) (step right) ≤
        perturbation left right

theorem LocalStabilityCertificate.domain_iterate
    {State : Type u}
    (certificate : LocalStabilityCertificate State)
    (steps : Nat)
    (state : State)
    (initial : certificate.domain state) :
    certificate.domain
      (iterateStep certificate.step steps state) := by
  induction steps with
  | zero =>
      exact initial
  | succ steps inductionHypothesis =>
      exact certificate.forwardInvariant
        (iterateStep certificate.step steps state)
        inductionHypothesis

theorem LocalStabilityCertificate.nonexpansive_iterate
    {State : Type u}
    (certificate : LocalStabilityCertificate State)
    (steps : Nat)
    (left right : State)
    (leftInDomain : certificate.domain left)
    (rightInDomain : certificate.domain right) :
    certificate.perturbation
        (iterateStep certificate.step steps left)
        (iterateStep certificate.step steps right) ≤
      certificate.perturbation left right := by
  induction steps with
  | zero =>
      exact Nat.le_refl _
  | succ steps inductionHypothesis =>
      exact Nat.le_trans
        (certificate.nonexpansive
          (iterateStep certificate.step steps left)
          (iterateStep certificate.step steps right)
          (certificate.domain_iterate steps left leftInDomain)
          (certificate.domain_iterate steps right rightInDomain))
        inductionHypothesis

def FiniteTimeAmplifies
    {State : Type u}
    (certificate : LocalStabilityCertificate State)
    (steps : Nat)
    (left right : State) : Prop :=
  certificate.perturbation left right <
    certificate.perturbation
      (iterateStep certificate.step steps left)
      (iterateStep certificate.step steps right)

theorem LocalStabilityCertificate.no_finite_time_amplification
    {State : Type u}
    (certificate : LocalStabilityCertificate State)
    (steps : Nat)
    (left right : State)
    (leftInDomain : certificate.domain left)
    (rightInDomain : certificate.domain right) :
    ¬ FiniteTimeAmplifies certificate steps left right := by
  intro amplification
  have bounded :=
    certificate.nonexpansive_iterate
      steps left right leftInDomain rightInDomain
  have impossible :
      certificate.perturbation left right <
        certificate.perturbation left right :=
    Nat.lt_of_lt_of_le amplification bounded
  exact (Nat.lt_irrefl _) impossible

/-- Recovery is represented as an explicit comparison to the shocked state,
    rather than inferred from a falling volatility series alone. -/
structure RecoveryCertificate (State : Type u) where
  perturbation : State → State → Nat
  baseline : State
  shocked : State
  recovered : State
  recoveredNoWorse :
    perturbation recovered baseline ≤
      perturbation shocked baseline

theorem RecoveryCertificate.sound
    {State : Type u}
    (certificate : RecoveryCertificate State) :
    certificate.perturbation
        certificate.recovered certificate.baseline ≤
      certificate.perturbation
        certificate.shocked certificate.baseline :=
  certificate.recoveredNoWorse

end LeanFinance.StateSpace
