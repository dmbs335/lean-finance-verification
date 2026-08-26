namespace LeanFinance.Epistemic

universe u v w x y z

/-- A hidden data history separates the observation key from the time at which
    that observation became available to the research process. -/
structure TemporalHistory (Index : Type u) (Value : Type v) where
  valueAt : Index → Option Value
  availableAt : Index → Nat

/-- What one history exposes at one cutoff. Values published after the cutoff
    are deliberately projected to `none`. -/
def observationThrough
    {Index : Type u}
    {Value : Type v}
    (history : TemporalHistory Index Value)
    (cutoff : Nat)
    (index : Index) : Option Value :=
  if history.availableAt index ≤ cutoff then
    history.valueAt index
  else
    none

/-- Two complete histories are indistinguishable through a cutoff when every
    value available by that cutoff is identical. They may differ arbitrarily in
    future observations and revisions. -/
def EquivalentThrough
    {Index : Type u}
    {Value : Type v}
    (cutoff : Nat)
    (left right : TemporalHistory Index Value) : Prop :=
  ∀ index,
    observationThrough left cutoff index =
      observationThrough right cutoff index

/-- A transformation is causal when equivalent input prefixes always produce
    equivalent output prefixes. -/
def CausalTransform
    {InputIndex : Type u}
    {InputValue : Type v}
    {OutputIndex : Type w}
    {OutputValue : Type x}
    (transform :
      TemporalHistory InputIndex InputValue →
        TemporalHistory OutputIndex OutputValue) : Prop :=
  ∀ cutoff left right,
    EquivalentThrough cutoff left right →
      EquivalentThrough cutoff (transform left) (transform right)

/-- Causal transformations compose. This is the temporal analogue of the
    certificate-composition law: local prefix guarantees yield a global prefix
    guarantee when the same transformed objects are connected. -/
theorem causal_transform_compose
    {InputIndex : Type u}
    {InputValue : Type v}
    {MiddleIndex : Type w}
    {MiddleValue : Type x}
    {OutputIndex : Type y}
    {OutputValue : Type z}
    (first :
      TemporalHistory InputIndex InputValue →
        TemporalHistory MiddleIndex MiddleValue)
    (second :
      TemporalHistory MiddleIndex MiddleValue →
        TemporalHistory OutputIndex OutputValue)
    (firstCausal : CausalTransform first)
    (secondCausal : CausalTransform second) :
    CausalTransform (fun history => second (first history)) := by
  intro cutoff left right equivalent
  exact secondCausal cutoff (first left) (first right)
    (firstCausal cutoff left right equivalent)

/-- A complete engine is prefix-noninterfering when fixed configuration and
    equal data prefixes force equal output prefixes. -/
def PrefixNoninterfering
    {Index : Type u}
    {Value : Type v}
    {Config : Type w}
    {Output : Type x}
    {Prefix : Type y}
    (run : Config → TemporalHistory Index Value → Output)
    (prefix : Nat → Output → Prefix) : Prop :=
  ∀ config cutoff left right,
    EquivalentThrough cutoff left right →
      prefix cutoff (run config left) =
        prefix cutoff (run config right)

/-- A prefix-safe engine remains prefix-safe after a causal feature or data
    transformation. -/
theorem noninterference_after_causal_transform
    {InputIndex : Type u}
    {InputValue : Type v}
    {OutputIndex : Type w}
    {OutputValue : Type x}
    {Config : Type y}
    {Output : Type z}
    {Prefix : Type u}
    (transform :
      TemporalHistory InputIndex InputValue →
        TemporalHistory OutputIndex OutputValue)
    (run : Config → TemporalHistory OutputIndex OutputValue → Output)
    (prefix : Nat → Output → Prefix)
    (transformCausal : CausalTransform transform)
    (runSafe : PrefixNoninterfering run prefix) :
    PrefixNoninterfering
      (fun config history => run config (transform history)) prefix := by
  intro config cutoff left right equivalent
  exact runSafe config cutoff (transform left) (transform right)
    (transformCausal cutoff left right equivalent)

/-- A first-divergence witness localizes the earliest corrupted output in a
    finite time prefix. -/
def FirstDivergenceAt
    {Output : Type u}
    (left right : Nat → Output)
    (cutoff time : Nat) : Prop :=
  time ≤ cutoff ∧
    left time ≠ right time ∧
      ∀ earlier,
        earlier < time → left earlier = right earlier

/-- Controlled worlds differing only in one future observation. -/
inductive ControlledWorld where
  | base
  | futureExtended
  deriving Repr, DecidableEq

inductive ControlledIndex where
  | past
  | future
  deriving Repr, DecidableEq

def controlledHistory
    (world : ControlledWorld) :
    TemporalHistory ControlledIndex Int :=
  { valueAt := fun index =>
      match index, world with
      | .past, _ => some 100
      | .future, .base => none
      | .future, .futureExtended => some 999
    availableAt := fun index =>
      match index with
      | .past => 1
      | .future => 10 }

theorem controlled_histories_equivalent_through_six :
    EquivalentThrough 6
      (controlledHistory .base)
      (controlledHistory .futureExtended) := by
  intro index
  cases index <;>
    simp [EquivalentThrough, observationThrough, controlledHistory]

/-- A deliberately noncausal engine that reads the future slot directly. -/
def futureLookingRun
    (_config : Unit)
    (history : TemporalHistory ControlledIndex Int) : Option Int :=
  history.valueAt .future

def identityPrefix (_cutoff : Nat) (output : Option Int) : Option Int :=
  output

/-- Constructive future-extension counterexample: the input prefixes are equal
    through time six, yet the engine's past-visible output changes. -/
theorem future_looking_run_is_not_prefix_noninterfering :
    ¬ PrefixNoninterfering futureLookingRun identityPrefix := by
  intro noninterfering
  have sameOutput := noninterfering () 6
    (controlledHistory .base)
    (controlledHistory .futureExtended)
    controlled_histories_equivalent_through_six
  simp [futureLookingRun, identityPrefix, controlledHistory] at sameOutput

end LeanFinance.Epistemic
