import LeanFinance.Types

namespace LeanFinance.ResearchIntegrity

/-- A pre-evaluation commitment to exact strategy code and parameters. -/
structure ResearchCommitment where
  strategyId : String
  codeHash : String
  parameterHash : String
  committedAt : Time
  deriving DecidableEq, Repr

def ResearchCommitment.Matches
    (commitment : ResearchCommitment)
    (strategyId codeHash parameterHash : String) : Prop :=
  commitment.strategyId = strategyId ∧
  commitment.codeHash = codeHash ∧
  commitment.parameterHash = parameterHash

def ResearchCommitment.ValidAt
    (commitment : ResearchCommitment)
    (decisionTime : Time) : Prop :=
  commitment.committedAt <= decisionTime ∧
  commitment.strategyId ≠ "" ∧
  commitment.codeHash ≠ "" ∧
  commitment.parameterHash ≠ ""

end LeanFinance.ResearchIntegrity
