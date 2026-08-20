namespace LeanFinance.Inference

universe u v w x

/-- Two latent states are observationally equivalent when the public
    observation map cannot distinguish them. -/
def ObservationallyEquivalent
    {Theta : Type u}
    {Observation : Type v}
    (observe : Theta → Observation)
    (left right : Theta) : Prop :=
  observe left = observe right

theorem observationallyEquivalent_refl
    {Theta : Type u}
    {Observation : Type v}
    (observe : Theta → Observation)
    (state : Theta) :
    ObservationallyEquivalent observe state state :=
  rfl

theorem observationallyEquivalent_symm
    {Theta : Type u}
    {Observation : Type v}
    {observe : Theta → Observation}
    {left right : Theta}
    (equivalent : ObservationallyEquivalent observe left right) :
    ObservationallyEquivalent observe right left :=
  equivalent.symm

theorem observationallyEquivalent_trans
    {Theta : Type u}
    {Observation : Type v}
    {observe : Theta → Observation}
    {first second third : Theta}
    (firstSecond : ObservationallyEquivalent observe first second)
    (secondThird : ObservationallyEquivalent observe second third) :
    ObservationallyEquivalent observe first third :=
  firstSecond.trans secondThird

/-- A target is point identified when it is constant on every observational
    equivalence class. This is the relevant notion for inverse games: the
    complete primitive need not be unique, but the prediction target may be. -/
def Identified
    {Theta : Type u}
    {Observation : Type v}
    {Target : Type w}
    (observe : Theta → Observation)
    (target : Theta → Target) : Prop :=
  ∀ left right,
    ObservationallyEquivalent observe left right →
      target left = target right

/-- The identified set is the collection of latent states compatible with one
    public observation. -/
def IdentifiedSet
    {Theta : Type u}
    {Observation : Type v}
    (observe : Theta → Observation)
    (observation : Observation) : Theta → Prop :=
  fun state => observe state = observation

theorem truth_mem_identifiedSet
    {Theta : Type u}
    {Observation : Type v}
    (observe : Theta → Observation)
    (state : Theta) :
    IdentifiedSet observe (observe state) state :=
  rfl

/-- A target is identified whenever it factors through the observation map. -/
theorem identified_of_factorization
    {Theta : Type u}
    {Observation : Type v}
    {Target : Type w}
    (observe : Theta → Observation)
    (target : Theta → Target)
    (decode : Observation → Target)
    (factor : ∀ state, target state = decode (observe state)) :
    Identified observe target := by
  intro left right sameObservation
  rw [factor left, factor right, sameObservation]

/-- A finer public observation cannot destroy identification. If the coarse
    observation can be recovered by forgetting part of the fine observation,
    every target identified under the coarse observation remains identified
    under the refinement. -/
theorem identified_of_observation_refinement
    {Theta : Type u}
    {CoarseObservation : Type v}
    {FineObservation : Type x}
    {Target : Type w}
    (coarse : Theta → CoarseObservation)
    (fine : Theta → FineObservation)
    (forget : FineObservation → CoarseObservation)
    (target : Theta → Target)
    (refines : ∀ state, coarse state = forget (fine state))
    (identified : Identified coarse target) :
    Identified fine target := by
  intro left right sameFineObservation
  apply identified left right
  change fine left = fine right at sameFineObservation
  change coarse left = coarse right
  calc
    coarse left = forget (fine left) := refines left
    _ = forget (fine right) := congrArg forget sameFineObservation
    _ = coarse right := (refines right).symm

/-- Any deterministic post-processing of an identified target remains
    identified. -/
theorem identified_postprocess
    {Theta : Type u}
    {Observation : Type v}
    {Target : Type w}
    {Output : Type x}
    {observe : Theta → Observation}
    {target : Theta → Target}
    (identified : Identified observe target)
    (postprocess : Target → Output) :
    Identified observe (fun state => postprocess (target state)) := by
  intro left right sameObservation
  exact congrArg postprocess (identified left right sameObservation)

/-- A single observationally equivalent pair with different target values is
    a constructive certificate of non-identifiability. -/
theorem not_identified_of_counterexample
    {Theta : Type u}
    {Observation : Type v}
    {Target : Type w}
    (observe : Theta → Observation)
    (target : Theta → Target)
    (left right : Theta)
    (sameObservation : ObservationallyEquivalent observe left right)
    (differentTarget : target left ≠ target right) :
    ¬ Identified observe target := by
  intro identified
  exact differentTarget (identified left right sameObservation)

end LeanFinance.Inference
