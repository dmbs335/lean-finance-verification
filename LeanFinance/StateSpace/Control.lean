import LeanFinance.StateSpace.Model

namespace LeanFinance.StateSpace

universe u v w

structure ControlledSystem
    (State : Type u)
    (Input : Type v) where
  step : State → Input → State

def applyControls
    {State : Type u}
    {Input : Type v}
    (system : ControlledSystem State Input) :
    List Input → State → State
  | [], state => state
  | input :: remaining, state =>
      applyControls system remaining
        (system.step state input)

theorem applyControls_append
    {State : Type u}
    {Input : Type v}
    (system : ControlledSystem State Input)
    (first second : List Input)
    (state : State) :
    applyControls system (first ++ second) state =
      applyControls system second
        (applyControls system first state) := by
  induction first generalizing state with
  | nil =>
      rfl
  | cons input remaining inductionHypothesis =>
      exact inductionHypothesis
        (state := system.step state input)

def Reachable
    {State : Type u}
    {Input : Type v}
    (system : ControlledSystem State Input)
    (source target : State) : Prop :=
  ∃ controls : List Input,
    applyControls system controls source = target

theorem reachable_refl
    {State : Type u}
    {Input : Type v}
    (system : ControlledSystem State Input)
    (state : State) :
    Reachable system state state := by
  exact ⟨[], rfl⟩

theorem reachable_trans
    {State : Type u}
    {Input : Type v}
    (system : ControlledSystem State Input)
    (source middle target : State)
    (sourceMiddle : Reachable system source middle)
    (middleTarget : Reachable system middle target) :
    Reachable system source target := by
  obtain ⟨firstControls, firstReaches⟩ := sourceMiddle
  obtain ⟨secondControls, secondReaches⟩ := middleTarget
  refine ⟨firstControls ++ secondControls, ?_⟩
  calc
    applyControls system (firstControls ++ secondControls) source =
        applyControls system secondControls
          (applyControls system firstControls source) :=
      applyControls_append system firstControls secondControls source
    _ = applyControls system secondControls middle := by
      rw [firstReaches]
    _ = target := secondReaches

structure ControlPlanCertificate
    {State : Type u}
    {Input : Type v}
    (system : ControlledSystem State Input)
    (source target : State) where
  controls : List Input
  reaches : applyControls system controls source = target

theorem ControlPlanCertificate.sound
    {State : Type u}
    {Input : Type v}
    {system : ControlledSystem State Input}
    {source target : State}
    (certificate :
      ControlPlanCertificate system source target) :
    Reachable system source target :=
  ⟨certificate.controls, certificate.reaches⟩

/-- Finite-horizon observability is stated constructively: a control sequence
    distinguishes two states when their complete observation traces differ. -/
structure PartiallyObservedSystem
    (State : Type u)
    (Input : Type v)
    (Observation : Type w) where
  step : State → Input → State
  observe : State → Observation

def observationTrace
    {State : Type u}
    {Input : Type v}
    {Observation : Type w}
    (system : PartiallyObservedSystem State Input Observation) :
    List Input → State → List Observation
  | [], state => [system.observe state]
  | input :: remaining, state =>
      system.observe state ::
        observationTrace system remaining
          (system.step state input)

def PairObservable
    {State : Type u}
    {Input : Type v}
    {Observation : Type w}
    (system : PartiallyObservedSystem State Input Observation)
    (left right : State) : Prop :=
  ∃ controls : List Input,
    observationTrace system controls left ≠
      observationTrace system controls right

structure PairObservabilityCertificate
    {State : Type u}
    {Input : Type v}
    {Observation : Type w}
    (system : PartiallyObservedSystem State Input Observation)
    (left right : State) where
  controls : List Input
  distinguishes :
    observationTrace system controls left ≠
      observationTrace system controls right

theorem PairObservabilityCertificate.sound
    {State : Type u}
    {Input : Type v}
    {Observation : Type w}
    {system : PartiallyObservedSystem State Input Observation}
    {left right : State}
    (certificate :
      PairObservabilityCertificate system left right) :
    PairObservable system left right :=
  ⟨certificate.controls, certificate.distinguishes⟩

end LeanFinance.StateSpace
