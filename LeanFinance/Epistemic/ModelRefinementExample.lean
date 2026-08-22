import LeanFinance.Epistemic.ModelRefinement

namespace LeanFinance.Epistemic.ModelRefinementExample

inductive OriginalAction where
  | publish
  deriving Repr, DecidableEq

structure OriginalState where
  published : Bool
  deriving Repr, DecidableEq

def originalWorkflow : FiniteWorkflow OriginalState OriginalAction :=
  {
    initial := { published := false }
    actions := [.publish]
    enabled := fun state _ action =>
      match action with
      | .publish => !state.published
    transition := fun state action =>
      match action with
      | .publish => { state with published := true }
    terminal := fun state => state.published
  }

inductive RefinedAction where
  | publish
  | tamper
  deriving Repr, DecidableEq

structure RefinedState where
  published : Bool
  tampered : Bool
  deriving Repr, DecidableEq

def refinedWorkflow : FiniteWorkflow RefinedState RefinedAction :=
  {
    initial := { published := false, tampered := false }
    actions := [.publish, .tamper]
    enabled := fun state _ action =>
      match action with
      | .publish => !state.published
      | .tamper => !state.published && !state.tampered
    transition := fun state action =>
      match action with
      | .publish => { state with published := true }
      | .tamper => { state with tampered := true }
    terminal := fun state => state.published
  }

def embedState (state : OriginalState) : RefinedState :=
  { published := state.published, tampered := false }

def embedAction : OriginalAction → RefinedAction
  | .publish => .publish

def conservativeRefinement :
    WorkflowRefinement originalWorkflow refinedWorkflow :=
  {
    embedState := embedState
    embedAction := embedAction
    initialPreserved := rfl
    enabledPreserved := by
      intro state prefix action
      cases action
      simp [originalWorkflow, refinedWorkflow, embedState, embedAction]
    transitionPreserved := by
      intro state action
      cases action
      rfl
    terminalPreserved := by
      intro state
      rfl
  }

def originalClaim (_state : OriginalState) : Bool :=
  true

def refinedClaim (state : RefinedState) : Bool :=
  !state.tampered

def claimPreservingRefinement :
    ClaimPreservingWorkflowRefinement
      originalWorkflow refinedWorkflow originalClaim refinedClaim :=
  {
    toWorkflowRefinement := conservativeRefinement
    claimPreserved := by
      intro state
      rfl
  }

theorem honest_publish_replay_preserved :
    replay refinedWorkflow [.publish] =
      some { published := true, tampered := false } := by
  have originalReplay :
      replay originalWorkflow [.publish] =
        some { published := true } := by
    decide
  have preserved :=
    conservativeRefinement.replay_preserved [.publish]
  rw [originalReplay] at preserved
  exact preserved

theorem refinement_adds_new_violating_trace :
    replay refinedWorkflow [.tamper, .publish] =
      some { published := true, tampered := true } ∧
    refinedClaim { published := true, tampered := true } = false := by
  decide

end LeanFinance.Epistemic.ModelRefinementExample
