import LeanFinance.Core
import LeanFinance.Inference.HiddenState

namespace LeanFinance.Inference

structure InverseGameProblem where
  observations : List ObservedMarketData
  candidateStates : List HiddenMarketState
  score : HiddenMarketState → Scalar

def BestExplainingState
    (problem : InverseGameProblem)
    (chosen : HiddenMarketState) : Prop :=
  chosen ∈ problem.candidateStates ∧
    ∀ alternative,
      alternative ∈ problem.candidateStates →
      problem.score alternative ≤ problem.score chosen

theorem explaining_state_is_a_candidate
    (problem : InverseGameProblem)
    (chosen : HiddenMarketState)
    (h : BestExplainingState problem chosen) :
    chosen ∈ problem.candidateStates :=
  h.1

end LeanFinance.Inference
