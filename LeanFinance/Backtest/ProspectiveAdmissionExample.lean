import LeanFinance.Backtest.ProspectiveAdmission

namespace LeanFinance.Backtest.ProspectiveAdmissionExample

open LeanFinance.Backtest

def plan : ProspectiveBacktestPlan :=
  { planId := "controlled-prospective-backtest"
    registeredAt := 10
    firstDecisionAt := 20
    outcomeStartAt := 20
    outcomeEndAt := 50
    codeDigest := 1
    parameterDigest := 2
    metricDigest := 3
    benchmarkDigest := 4
    costModelDigest := 5
    universeDigest := 6
    primaryTrialId := 11
    registeredTrialIds := [11, 12]
    minimumResultLowerBps := 3 }

def outcome : ProspectiveOutcome :=
  { windowStartAt := 20
    windowEndAt := 50
    availableAt := 60
    resultLowerBps := 5
    strictPointInTime := true }

def certificate : ProspectiveBacktestAdmissionCertificate :=
  { plan := plan
    outcome := outcome
    executedTrialIds := [11, 12]
    selectedTrialId := 11
    preregistered := by decide
    outcomeMature := by decide
    strictPointInTime := rfl
    codeBound := True
    parametersBound := True
    metricBound := True
    benchmarkBound := True
    costModelBound := True
    universeBound := True
    completeTrialLedger := rfl
    primaryTrialSelected := rfl
    lowerBoundPasses := by decide }

theorem controlled_certificate_passes_every_gate :
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
  certificate.all_admission_gates

theorem controlled_pending_plan_remains_pending :
    prospectiveAdmissionDecision true false false false = .pending := by
  decide

theorem post_hoc_plan_is_rejected :
    prospectiveAdmissionDecision false true true true = .rejected := by
  decide

end LeanFinance.Backtest.ProspectiveAdmissionExample
