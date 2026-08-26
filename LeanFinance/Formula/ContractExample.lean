import LeanFinance.Formula.Contract

namespace LeanFinance.Formula.ContractExample

open LeanFinance.Formula

def hedgeScaleDefinition : FormulaDefinition :=
  { formulaId := "hedge-scale-percent-v1"
    expressionHash := "expression-hash"
    implementationHash := "implementation-hash"
    registeredAt := 5 }

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
    claimedDenominator := 4
    outputArtifactHash := "hedge-scale-output"
    outputGeneratedAt := 9 }

def validCertificate : FormulaApplicationCertificate :=
  { definition := hedgeScaleDefinition
    application := validApplication
    valid :=
      { definitionMatched := by
          simp [HedgeScaleApplication.DefinitionMatched,
            validApplication, hedgeScaleDefinition]
        definitionAvailable := by
          simp [HedgeScaleApplication.DefinitionAvailable,
            validApplication, hedgeScaleDefinition]
        inputsAvailable := by
          simp [HedgeScaleApplication.InputsAvailable,
            validApplication, currentRisk, hedgeRisk, riskPercentage]
        valuationsNotFuture := by
          simp [HedgeScaleApplication.ValuationsNotFuture,
            validApplication, currentRisk, hedgeRisk, riskPercentage]
        outputAvailable := by
          simp [HedgeScaleApplication.OutputAvailable, validApplication]
        unitsValid := by
          simp [HedgeScaleApplication.UnitsValid,
            validApplication, currentRisk, hedgeRisk, riskPercentage]
        valuationAligned := by
          simp [HedgeScaleApplication.ValuationAligned,
            validApplication, currentRisk, hedgeRisk]
        modelAligned := by
          simp [HedgeScaleApplication.ModelAligned,
            validApplication, currentRisk, hedgeRisk]
        domainValid := by
          simp [HedgeScaleApplication.DomainValid,
            validApplication, hedgeRisk]
        artifactsBound := by
          simp [HedgeScaleApplication.ArtifactsBound,
            validApplication, currentRisk, hedgeRisk, riskPercentage,
            NonEmptyString]
        resultBound := by
          simp [HedgeScaleApplication.ResultBound,
            validApplication, currentRisk, hedgeRisk, riskPercentage] } }

theorem valid_scale_is_three_quarters :
    validApplication.claimedNumerator = 3 ∧
      validApplication.claimedDenominator = 4 := by
  rfl

def futureCurrentRisk : FormulaInput :=
  { currentRisk with availableAt := 11 }

def futureApplication : HedgeScaleApplication :=
  { validApplication with currentRisk := futureCurrentRisk }

theorem future_application_matches_formula_definition :
    HedgeScaleApplication.DefinitionMatched
      futureApplication hedgeScaleDefinition := by
  simp [HedgeScaleApplication.DefinitionMatched,
    futureApplication, futureCurrentRisk, validApplication,
    hedgeScaleDefinition]

theorem future_application_result_is_algebraically_correct :
    HedgeScaleApplication.ResultBound futureApplication := by
  simp [HedgeScaleApplication.ResultBound,
    futureApplication, futureCurrentRisk, validApplication,
    currentRisk, hedgeRisk, riskPercentage]

theorem future_application_is_not_valid :
    ¬ HedgeScaleApplication.Valid
      futureApplication hedgeScaleDefinition := by
  intro valid
  have available : (11 : Nat) ≤ 10 := by
    simpa [HedgeScaleApplication.InputsAvailable,
      futureApplication, futureCurrentRisk, validApplication,
      currentRisk, hedgeRisk, riskPercentage] using
      valid.inputsAvailable.1
  exact (by decide : ¬ (11 : Nat) ≤ 10) available

/-- A correct registered formula and an algebraically correct result do not imply
    a valid financial application: an input can still arrive after the decision
    it purports to support. -/
theorem formula_correctness_does_not_imply_application_correctness :
    ∃ application : HedgeScaleApplication,
      HedgeScaleApplication.DefinitionMatched
          application hedgeScaleDefinition ∧
        HedgeScaleApplication.ResultBound application ∧
          ¬ HedgeScaleApplication.Valid application hedgeScaleDefinition :=
  ⟨futureApplication,
    future_application_matches_formula_definition,
    future_application_result_is_algebraically_correct,
    future_application_is_not_valid⟩

end LeanFinance.Formula.ContractExample
