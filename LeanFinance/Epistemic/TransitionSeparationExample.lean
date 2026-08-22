import LeanFinance.Epistemic.TransitionSeparation

namespace LeanFinance.Epistemic.TransitionSeparationExample

structure State where
  tampered : Bool
  published : Bool
  deriving Repr, DecidableEq

inductive Action where
  | tamper
  | publish
  deriving Repr, DecidableEq

def enabled (state : State) (_prefix : List Action) : Action → Bool
  | .tamper => !state.tampered && !state.published
  | .publish => !state.published

def transition (state : State) : Action → State
  | .tamper => { state with tampered := true }
  | .publish => { state with published := true }

def workflow : FiniteWorkflow State Action :=
  {
    initial := { tampered := false, published := false }
    actions := [.tamper, .publish]
    enabled := enabled
    transition := transition
    terminal := fun state => state.published
  }

def safe (state : State) : Bool :=
  !state.tampered

inductive Channel where
  | resultBundle
  | rfc3161Timestamp
  | tamperReceipt
  deriving Repr, DecidableEq

/-- Publication artifacts are equal for both executions. The receipt is tied to
the actual replay result and therefore crosses the mutation boundary. -/
def receipt : Channel → List Action → Bool
  | .resultBundle, _ => false
  | .rfc3161Timestamp, _ => false
  | .tamperReceipt, trace =>
      match replay workflow trace with
      | none => false
      | some finalState => finalState.tampered

def selectedDownstream : Channel → Prop
  | .resultBundle | .rfc3161Timestamp => True
  | .tamperReceipt => False

def selectedReceipt : Channel → Prop
  | .tamperReceipt => True
  | _ => False

def honest : ExecutedTrace workflow :=
  {
    trace := [.publish]
    finalState := { tampered := false, published := true }
    replayed := by decide
  }

def attack : ExecutedTrace workflow :=
  {
    trace := [.tamper, .publish]
    finalState := { tampered := true, published := true }
    replayed := by decide
  }

theorem honest_safe : honest.Safe safe := by
  decide

theorem attack_unsafe : safe attack.finalState = false := by
  decide

/-- Once the state is tampered, every valid continuation remains tampered. -/
theorem replayFrom_preserves_tampered :
    ∀ state prefix trace finalState,
      state.tampered = true →
      replayFrom workflow state prefix trace = some finalState →
      finalState.tampered = true := by
  intro state prefix trace
  induction trace generalizing state prefix with
  | nil =>
      intro finalState stateTampered replayed
      have stateEq : state = finalState := by
        simpa [replayFrom] using replayed
      subst finalState
      exact stateTampered
  | cons action rest ih =>
      intro finalState stateTampered replayed
      by_cases terminalTrue : workflow.terminal state = true
      · simp [replayFrom, terminalTrue] at replayed
      · have terminalFalse : workflow.terminal state = false :=
          Bool.eq_false_of_not_eq_true terminalTrue
        by_cases actionEnabled : workflow.enabled state prefix action = true
        · have tailReplay :
              replayFrom workflow
                  (workflow.transition state action)
                  (prefix ++ [action]) rest =
                some finalState := by
            simpa [replayFrom, terminalFalse, actionEnabled] using replayed
          have nextTampered :
              (workflow.transition state action).tampered = true := by
            cases action <;>
              simp [workflow, transition, stateTampered]
          exact ih
            (workflow.transition state action)
            (prefix ++ [action]) finalState
            nextTampered tailReplay
        · have actionDisabled : workflow.enabled state prefix action = false :=
            Bool.eq_false_of_not_eq_true actionEnabled
          simp [replayFrom, terminalFalse, actionDisabled] at replayed

/-- Safe traces never emit the tamper receipt. -/
theorem tamper_receipt_safe_specific :
    SafeSpecificReceipt workflow safe receipt .tamperReceipt := by
  intro history historySafe
  have finalClean : history.finalState.tampered = false := by
    cases tamperedValue : history.finalState.tampered <;>
      simp [ExecutedTrace.Safe, safe, tamperedValue] at historySafe ⊢
  simp [receipt, history.replayed, finalClean]

/-- Every first safe-to-unsafe transition in this workflow is the tamper action,
and its receipt survives all valid continuations. -/
theorem tamper_receipt_persistent_cover :
    PersistentFirstViolationCover
      workflow safe receipt selectedReceipt := by
  intro witness
  have actionIsTamper : witness.action = .tamper := by
    cases actionCase : witness.action with
    | tamper => rfl
    | publish =>
        cases sourceTampered : witness.source.tampered <;>
          simp [safe, workflow, transition, actionCase, sourceTampered]
            at witness.sourceSafe witness.targetUnsafe
  subst witness.action
  refine ⟨.tamperReceipt, by simp [selectedReceipt],
    tamper_receipt_safe_specific, ?_⟩
  intro suffix finalState fullReplay
  have expanded :
      replayFrom workflow witness.source witness.prefix
          (.tamper :: suffix) = some finalState := by
    have replayAppend :=
      replay_append workflow witness.prefix (.tamper :: suffix)
    rw [replayAppend, witness.sourceReplayed] at fullReplay
    exact fullReplay
  have terminalFalse : workflow.terminal witness.source = false := by
    by_cases terminalTrue : workflow.terminal witness.source = true
    · simp [replayFrom, terminalTrue] at expanded
    · exact Bool.eq_false_of_not_eq_true terminalTrue
  have tailReplay :
      replayFrom workflow
          (workflow.transition witness.source .tamper)
          (witness.prefix ++ [.tamper]) suffix =
        some finalState := by
    simpa [replayFrom, terminalFalse, witness.actionEnabled] using expanded
  have targetTampered :
      (workflow.transition witness.source .tamper).tampered = true := by
    cases targetValue :
        (workflow.transition witness.source .tamper).tampered <;>
      simp [safe, targetValue] at witness.targetUnsafe ⊢
  have finalTampered : finalState.tampered = true :=
    replayFrom_preserves_tampered
      (workflow.transition witness.source .tamper)
      (witness.prefix ++ [.tamper]) suffix finalState
      targetTampered tailReplay
  simp [receipt, fullReplay, finalTampered]

/-- Result artifacts and timestamps are silent across the first violating
transition, so they cannot verify the safety claim. -/
theorem downstream_evidence_cannot_verify_tampering :
    ¬ ChannelSelectionVerifies
      (fun evidenceChannel history =>
        receipt evidenceChannel history.trace)
      selectedDownstream
      (ExecutedTrace.Safe safe) := by
  apply silent_violation_pair_implies_unverifiable
    workflow safe receipt selectedDownstream
    honest attack honest_safe attack_unsafe
  intro evidenceChannel chosen
  cases evidenceChannel <;>
    simp [selectedDownstream, receipt, honest, attack] at chosen ⊢

/-- A persistent, safe-specific receipt at the mutation boundary verifies the
safety claim for every successfully executed trace, not just the two examples. -/
theorem tamper_receipt_verifies_all_executed_traces :
    ChannelSelectionVerifies
      (fun evidenceChannel history =>
        receipt evidenceChannel history.trace)
      selectedReceipt
      (ExecutedTrace.Safe safe) :=
  persistent_first_violation_cover_implies_verifiable
    workflow safe receipt selectedReceipt
    (by decide)
    tamper_receipt_persistent_cover

end LeanFinance.Epistemic.TransitionSeparationExample
