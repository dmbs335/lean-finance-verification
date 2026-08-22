namespace LeanFinance.Epistemic

universe u v

/-- A deterministic finite-action workflow. `enabled` may depend on the complete
    action prefix, allowing bounded occurrence and protocol-state contracts to
    be represented without hiding them in the external explorer. -/
structure FiniteWorkflow (State : Type u) (Action : Type v) where
  initial : State
  actions : List Action
  enabled : State → List Action → Action → Bool
  transition : State → Action → State
  terminal : State → Bool

/-- Replay one action sequence while preserving the executed prefix used by the
    workflow's enablement predicate. Actions after a terminal state are invalid. -/
def replayFrom
    {State : Type u}
    {Action : Type v}
    (workflow : FiniteWorkflow State Action) :
    State → List Action → List Action → Option State
  | state, _executedPrefix, [] => some state
  | state, executedPrefix, action :: rest =>
      if workflow.terminal state then
        none
      else if workflow.enabled state executedPrefix action then
        replayFrom workflow
          (workflow.transition state action)
          (executedPrefix ++ [action]) rest
      else
        none

/-- Replay a trace from the workflow's declared initial state. -/
def replay
    {State : Type u}
    {Action : Type v}
    (workflow : FiniteWorkflow State Action)
    (trace : List Action) : Option State :=
  replayFrom workflow workflow.initial [] trace

/-- A trace is terminal when it replays successfully and ends in a terminal
    state. -/
def isTerminalTrace
    {State : Type u}
    {Action : Type v}
    (workflow : FiniteWorkflow State Action)
    (trace : List Action) : Bool :=
  match replay workflow trace with
  | none => false
  | some state => workflow.terminal state

/-- Extend one nonterminal valid trace by every enabled declared action. -/
def extendTrace
    {State : Type u}
    {Action : Type v}
    (workflow : FiniteWorkflow State Action)
    (trace : List Action) : List (List Action) :=
  match replay workflow trace with
  | none => []
  | some state =>
      if workflow.terminal state then
        []
      else
        workflow.actions.filterMap (fun action =>
          if workflow.enabled state trace action then
            some (trace ++ [action])
          else
            none)

/-- All valid nonterminal-or-terminal traces of exactly one depth. Terminal
    traces have no successors, so they do not reappear at later depths. -/
def tracesAtDepth
    {State : Type u}
    {Action : Type v}
    (workflow : FiniteWorkflow State Action) :
    Nat → List (List Action)
  | 0 => [[]]
  | depth + 1 =>
      (tracesAtDepth workflow depth).flatMap
        (extendTrace workflow)

/-- Terminal traces at one exact depth. -/
def terminalTracesAtDepth
    {State : Type u}
    {Action : Type v}
    (workflow : FiniteWorkflow State Action)
    (depth : Nat) : List (List Action) :=
  (tracesAtDepth workflow depth).filter
    (isTerminalTrace workflow)

/-- Enumerate every terminal trace up to and including `maxDepth`. -/
def enumerateTerminalTraces
    {State : Type u}
    {Action : Type v}
    (workflow : FiniteWorkflow State Action) :
    Nat → List (List Action)
  | 0 => terminalTracesAtDepth workflow 0
  | depth + 1 =>
      enumerateTerminalTraces workflow depth ++
        terminalTracesAtDepth workflow (depth + 1)

end LeanFinance.Epistemic
