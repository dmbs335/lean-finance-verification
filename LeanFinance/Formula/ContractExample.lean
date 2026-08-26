import LeanFinance.Formula.Contract

namespace LeanFinance.Formula.ContractExample

open LeanFinance.Formula

def hedgeScaleDefinition : FormulaDefinition :=
  { formulaId := "hedge-scale-percent-v1"
    expressionHash := "expression-hash"
    implementationHash := "implementation-hash" }

def currentRisk : FormulaInput :=
  { artifactHash := "current-risk-artifact"
    availableAt := 8
    valuationAt := 8
    modelId := "risk-model"
    modelVersion := "v1"
    unit := .usdRisk
    value := 120 }

def hedgeRisk : FormulaInput :=
  { artifactHash := "hedge-risk-artifact"
    availableAt := 8
    valuationAt := 8
    modelId := "risk-model"
    modelVersion := "v1"
    unit := .usdRisk
    value := -80 }

def riskPercentage : FormulaInput :=
  { artifactHash := "risk-percentage-artifact"
    availableAt := 7
    valuationAt := 8
    modelId := "registered-parameter"
    modelVersion := "v1"
    unit := .percent
    value := 50 }

def validApplication : HedgeScaleApplication :=
  { formulaId := "hedge-scale-percent-v1"
    expressionHash := "expression-hash"
    implementationHash := "implementation-hash"
    decisionAt := 10
    currentRisk := currentRisk
    hedgeRisk := hedgeRisk
    riskPercentage := riskPercentage
    claimedNumerator := 3
    claimedDenominator := 4 }

def validCertificate : FormulaApplicationCertificate :=
  { definition := hedgeScaleDefinition
    application := validApplication
    valid :=
      { definitionMatched := by decide
        inputsAvailable := by decide
        valuationsNotFuture := by decide
        unitsValid := by decide
        valuationAligned := by decide
        modelAligned := by decide
        domainValid := by decide
        artifactsBound := by decide
        resultBound := by decide } }

theorem valid_scale_is_three_quarters :
    validApplication.claimedNumerator = 3 ∧
      validApplication.claimedDenominator = 4 := by
  decide

def futureCurrentRisk : FormulaInput :=
  { currentRisk with availableAt := 11 }

def futureApplication : HedgeScaleApplication :=
  { validApplication with currentRisk := futureCurrentRisk }

theorem future_application_matches_formula_definition :
    futureApplication.DefinitionMatched hedgeScaleDefinition := by
  decide

theorem future_application_result_is_algebraically_correct :
    futureApplication.ResultBound := by
  decide

theorem future_application_is_not_valid :
    ¬ futureApplication.Valid hedgeScaleDefinition := by
  intro valid
  have available := valid.inputsAvailable.1
  exact (by decide : ¬ (11 : Nat) ≤ 10) available

/-- A correct formula definition and algebraically correct number do not imply a
    valid financial application. The input may still be from the future. -/
theorem formula_correctness_does_not_imply_application_correctness :
    ∃ application,
      application.DefinitionMatched hedgeScaleDefinition ∧
        application.ResultBound ∧
          ¬ application.Valid hedgeScaleDefinition :=
  ⟨futureApplication,
    future_application_matches_formula_definition,
    future_application_result_is_algebraically_correct,
    future_application_is_not_valid⟩

end LeanFinance.Formula.ContractExample
