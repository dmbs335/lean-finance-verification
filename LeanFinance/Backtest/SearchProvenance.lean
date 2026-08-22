import LeanFinance.Backtest.Artifact

namespace LeanFinance.Backtest

/-- A complete search session records the exploration process, not only the
    winning trial. This prevents a certificate from hiding discarded trials. -/
structure SearchSession where
  sessionId : String
  strategyId : String
  startedAt : Timestamp
  finishedAt : Timestamp
  budget : Nat
  deriving Repr

structure SearchTrial where
  sessionId : String
  trialId : String
  parameters : ArtifactRef .parameterSet
  code : ArtifactRef .sourceCode
  randomSeed : Nat
  executedAt : Timestamp
  succeeded : Bool
  deriving Repr

structure SearchLedgerCommitment where
  session : SearchSession
  trials : List SearchTrial
  committedAt : Timestamp
  commitment : ArtifactRef .searchLedger
  deriving Repr

/-- The committed search must account for every trial within the declared
    search budget. -/
def SearchBudgetRespected
    (commitment : SearchLedgerCommitment) : Prop :=
  commitment.trials.length ≤ commitment.session.budget

/-- The selected trial must be part of the committed exploration history. -/
def SelectedTrialAccounted
    (commitment : SearchLedgerCommitment)
    (selected : SearchTrial) : Prop :=
  selected ∈ commitment.trials

/-- A winning trial cannot be considered preregistered unless the search
    process containing it was committed. -/
structure SearchProvenanceCertificate
    (commitment : SearchLedgerCommitment)
    (selected : SearchTrial) : Prop where
  budgetValid : SearchBudgetRespected commitment
  selectedRecorded : SelectedTrialAccounted commitment selected
  commitmentBound : commitment.commitment.Valid

end LeanFinance.Backtest
