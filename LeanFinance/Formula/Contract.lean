import LeanFinance.Core

namespace LeanFinance.Formula

/-- Small registered unit vocabulary for the first proof-carrying formula
    contract. Additional dimensions can be introduced without changing the
    application theorem. -/
inductive UnitTag where
  | scalar
  | percent
  | basisPoints
  | usdRisk
  | eurRisk
  deriving Repr, DecidableEq

structure FormulaDefinition where
  formulaId : String
  expressionHash : ContentHash
  implementationHash : ContentHash
  deriving Repr, DecidableEq

/-- One exact formula input and the metadata required to decide whether it was
    admissible at the application boundary. -/
structure FormulaInput where
  artifactHash : ContentHash
  availableAt : Timestamp
  valuationAt : Timestamp
  modelId : String
  modelVersion : String
  unit : UnitTag
  value : Int
  deriving Repr, DecidableEq

structure HedgeScaleApplication where
  formulaId : String
  expressionHash : ContentHash
  implementationHash : ContentHash
  decisionAt : Timestamp
  currentRisk : FormulaInput
  hedgeRisk : FormulaInput
  riskPercentage : FormulaInput
  claimedNumerator : Int
  claimedDenominator : Int
  deriving Repr, DecidableEq

namespace HedgeScaleApplication

def DefinitionMatched
    (definition : FormulaDefinition)
    (application : HedgeScaleApplication) : Prop :=
  application.formulaId = definition.formulaId ∧
    application.expressionHash = definition.expressionHash ∧
      application.implementationHash = definition.implementationHash

def InputsAvailable (application : HedgeScaleApplication) : Prop :=
  application.currentRisk.availableAt ≤ application.decisionAt ∧
    application.hedgeRisk.availableAt ≤ application.decisionAt ∧
      application.riskPercentage.availableAt ≤ application.decisionAt

def ValuationsNotFuture (application : HedgeScaleApplication) : Prop :=
  application.currentRisk.valuationAt ≤ application.decisionAt ∧
    application.hedgeRisk.valuationAt ≤ application.decisionAt ∧
      application.riskPercentage.valuationAt ≤ application.decisionAt

def UnitsValid (application : HedgeScaleApplication) : Prop :=
  application.currentRisk.unit = application.hedgeRisk.unit ∧
    (application.currentRisk.unit = .usdRisk ∨
      application.currentRisk.unit = .eurRisk) ∧
        application.riskPercentage.unit = .percent

def ValuationAligned (application : HedgeScaleApplication) : Prop :=
  application.currentRisk.valuationAt = application.hedgeRisk.valuationAt

def ModelAligned (application : HedgeScaleApplication) : Prop :=
  application.currentRisk.modelId = application.hedgeRisk.modelId ∧
    application.currentRisk.modelVersion =
      application.hedgeRisk.modelVersion

def DomainValid (application : HedgeScaleApplication) : Prop :=
  application.hedgeRisk.value ≠ 0 ∧
    application.claimedDenominator ≠ 0

def ArtifactsBound (application : HedgeScaleApplication) : Prop :=
  NonEmptyString application.currentRisk.artifactHash ∧
    NonEmptyString application.hedgeRisk.artifactHash ∧
      NonEmptyString application.riskPercentage.artifactHash

/-- The claimed rational result equals

      -(current risk × whole-percent value) / (hedge risk × 100)

    without requiring division or normalization in the trusted theorem. -/
def ResultBound (application : HedgeScaleApplication) : Prop :=
  application.claimedNumerator *
      (application.hedgeRisk.value * 100) =
    (-application.currentRisk.value * application.riskPercentage.value) *
      application.claimedDenominator

/-- Formula correctness and application correctness are separate. A valid
    application carries definition, temporal, unit, model, domain, artifact, and
    output-binding obligations. -/
structure Valid
    (definition : FormulaDefinition)
    (application : HedgeScaleApplication) : Prop where
  definitionMatched : application.DefinitionMatched definition
  inputsAvailable : application.InputsAvailable
  valuationsNotFuture : application.ValuationsNotFuture
  unitsValid : application.UnitsValid
  valuationAligned : application.ValuationAligned
  modelAligned : application.ModelAligned
  domainValid : application.DomainValid
  artifactsBound : application.ArtifactsBound
  resultBound : application.ResultBound

end HedgeScaleApplication

structure FormulaApplicationCertificate where
  definition : FormulaDefinition
  application : HedgeScaleApplication
  valid : application.Valid definition

namespace FormulaApplicationCertificate

theorem temporal_inputs_available
    (certificate : FormulaApplicationCertificate) :
    certificate.application.InputsAvailable :=
  certificate.valid.inputsAvailable

theorem units_are_valid
    (certificate : FormulaApplicationCertificate) :
    certificate.application.UnitsValid :=
  certificate.valid.unitsValid

theorem result_is_bound_to_inputs
    (certificate : FormulaApplicationCertificate) :
    certificate.application.ResultBound :=
  certificate.valid.resultBound

end FormulaApplicationCertificate

end LeanFinance.Formula
