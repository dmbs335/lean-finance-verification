import LeanFinance.Backtest.PointInTimeData

namespace LeanFinance.Backtest

/-- A prospective backtest plan fixes its causal and evaluation boundary before
    the first decision and before the untouched outcome window begins. Digests
    stand for exact code, parameters, metrics, benchmark, cost, and universe
    artifacts verified by the external adapter. -/
structure ProspectiveBacktestPlan where
  planId : String
  registeredAt : Timestamp
  firstDecisionAt : Timestamp
  outcomeStartAt : Timestamp
  outcomeEndAt : Timestamp
  codeDigest : Nat
  parameterDigest : Nat
  metricDigest : Nat
  benchmarkDigest : Nat
  costModelDigest : Nat
  universeDigest : Nat
  primaryTrialId : Nat
  registeredTrialIds : List Nat
  minimumResultLowerBps : Int
  deriving Repr, DecidableEq

namespace ProspectiveBacktestPlan

def Preregistered (plan : ProspectiveBacktestPlan) : Prop :=
  plan.registeredAt < plan.firstDecisionAt ∧
    plan.firstDecisionAt ≤ plan.outcomeStartAt ∧
      plan.outcomeStartAt < plan.outcomeEndAt

end ProspectiveBacktestPlan

structure ProspectiveOutcome where
  windowStartAt : Timestamp
  windowEndAt : Timestamp
  availableAt : Timestamp
  resultLowerBps : Int
  strictPointInTime : Bool
  deriving Repr, DecidableEq

namespace ProspectiveOutcome

def MatureFor
    (outcome : ProspectiveOutcome)
    (plan : ProspectiveBacktestPlan) : Prop :=
  outcome.windowStartAt = plan.outcomeStartAt ∧
    outcome.windowEndAt = plan.outcomeEndAt ∧
      plan.outcomeEndAt ≤ outcome.availableAt

end ProspectiveOutcome

/-- Proof-carrying admission after the untouched window has matured. The trial
    ledger and all evaluation contracts must remain exactly bound to the plan. -/
structure ProspectiveBacktestAdmissionCertificate where
  plan : ProspectiveBacktestPlan
  outcome : ProspectiveOutcome
  executedTrialIds : List Nat
  selectedTrialId : Nat
  preregistered : plan.Preregistered
  outcomeMature : outcome.MatureFor plan
  strictPointInTime : outcome.strictPointInTime = true
  codeBound : Prop
  parametersBound : Prop
  metricBound : Prop
  benchmarkBound : Prop
  costModelBound : Prop
  universeBound : Prop
  completeTrialLedger : executedTrialIds = plan.registeredTrialIds
  primaryTrialSelected : selectedTrialId = plan.primaryTrialId
  lowerBoundPasses :
    plan.minimumResultLowerBps ≤ outcome.resultLowerBps

namespace ProspectiveBacktestAdmissionCertificate

theorem all_admission_gates
    (certificate : ProspectiveBacktestAdmissionCertificate) :
    certificate.plan.Preregistered ∧
      certificate.outcome.MatureFor certificate.plan ∧
        certificate.outcome.strictPointInTime = true ∧
          certificate.codeBound ∧
            certificate.parametersBound ∧
              certificate.metricBound ∧
                certificate.benchmarkBound ∧
                  certificate.costModelBound ∧
                    certificate.universeBound ∧
                      certificate.executedTrialIds =
                        certificate.plan.registeredTrialIds ∧
                        certificate.selectedTrialId =
                          certificate.plan.primaryTrialId ∧
                          certificate.plan.minimumResultLowerBps ≤
                            certificate.outcome.resultLowerBps :=
  ⟨certificate.preregistered,
    certificate.outcomeMature,
    certificate.strictPointInTime,
    certificate.codeBound,
    certificate.parametersBound,
    certificate.metricBound,
    certificate.benchmarkBound,
    certificate.costModelBound,
    certificate.universeBound,
    certificate.completeTrialLedger,
    certificate.primaryTrialSelected,
    certificate.lowerBoundPasses⟩

end ProspectiveBacktestAdmissionCertificate

inductive ProspectiveAdmissionDecision where
  | pending
  | admitted
  | rejected
  deriving Repr, DecidableEq

/-- Fail-closed executable stage semantics. Invalid registration is rejected;
    a valid plan with no outcome is pending; a presented outcome must already be
    mature and pass every outcome gate. -/
def prospectiveAdmissionDecision
    (structuralReady outcomePresent outcomeMature outcomePass : Bool) :
    ProspectiveAdmissionDecision :=
  if structuralReady then
    if outcomePresent then
      if outcomeMature && outcomePass then .admitted else .rejected
    else
      .pending
  else
    .rejected

theorem admitted_requires_every_boolean_gate
    (structuralReady outcomePresent outcomeMature outcomePass : Bool)
    (admitted :
      prospectiveAdmissionDecision structuralReady outcomePresent
        outcomeMature outcomePass = .admitted) :
    structuralReady = true ∧
      outcomePresent = true ∧
        outcomeMature = true ∧
          outcomePass = true := by
  cases structuralReady <;> cases outcomePresent <;>
    cases outcomeMature <;> cases outcomePass <;>
      simp [prospectiveAdmissionDecision] at admitted ⊢

theorem pending_requires_ready_plan_and_absent_outcome
    (structuralReady outcomePresent outcomeMature outcomePass : Bool)
    (pending :
      prospectiveAdmissionDecision structuralReady outcomePresent
        outcomeMature outcomePass = .pending) :
    structuralReady = true ∧ outcomePresent = false := by
  cases structuralReady <;> cases outcomePresent <;>
    cases outcomeMature <;> cases outcomePass <;>
      simp [prospectiveAdmissionDecision] at pending ⊢

theorem immature_presented_outcome_is_not_admitted
    (structuralReady outcomePass : Bool) :
    prospectiveAdmissionDecision structuralReady true false outcomePass ≠
      .admitted := by
  cases structuralReady <;> cases outcomePass <;>
    decide

end LeanFinance.Backtest
