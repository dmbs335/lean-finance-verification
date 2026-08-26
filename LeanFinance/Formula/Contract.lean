import LeanFinance.Core

namespace LeanFinance.Formula

/-- Registered unit vocabulary for the initial proof-carrying financial formula
    contract. Unit compatibility is an application obligation, not a convention
    hidden inside one implementation. -/
inductive UnitTag where
  | scalar
  | percent
  | basisPoints
  | usdRisk
  | eurRisk
  deriving Repr, DecidableEq

/-- Formula identity is bound to both its mathematical expression and executable
    implementation, and must be registered before use. -/
structure FormulaDefinition where
  formulaId : String
  expressionHash : ContentHash
  implementationHash : ContentHash
  registeredAt : Timestamp
  deriving Repr, DecidableEq

/-- One exact input together with the metadata needed to decide whether the
    value was admissible at the financial decision boundary. -/
structure FormulaInput where
  artifactHash : ContentHash
  availableAt : Timestamp
  valuationAt : Timestamp
  modelId : String
  modelVersion : String
  unit : UnitTag
  value : Int
  deriving Repr, DecidableEq

/-- Application of

      -(currentRisk / hedgeRisk) × riskPercentage / 100

    represented as an exact rational claim. -/
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
  outputArtifactHash : ContentHash
  outputGeneratedAt : Timestamp
  deriving Repr, DecidableEq

namespace HedgeScaleApplication

/-- The application names the exact registered expression and executable
    implementation. -/
def DefinitionMatched
    (application : HedgeScaleApplication)
    (definition : FormulaDefinition) : Prop :=
  application.formulaId = definition.formulaId ∧
    application.expressionHash = definition.expressionHash ∧
      application.implementationHash = definition.implementationHash

/-- The formula itself was registered before the decision. -/
def DefinitionAvailable
    (application : HedgeScaleApplication)
    (definition : FormulaDefinition) : Prop :=
  definition.registeredAt ≤ application.decisionAt

/-- Every consumed value was available by the decision cutoff. -/
def InputsAvailable (application : HedgeScaleApplication) : Prop :=
  application.currentRisk.availableAt ≤ application.decisionAt ∧
    application.hedgeRisk.availableAt ≤ application.decisionAt ∧
      application.riskPercentage.availableAt ≤ application.decisionAt

/-- Valuation timestamps cannot be after the decision they support. -/
def ValuationsNotFuture (application : HedgeScaleApplication) : Prop :=
  application.currentRisk.valuationAt ≤ application.decisionAt ∧
    application.hedgeRisk.valuationAt ≤ application.decisionAt ∧
      application.riskPercentage.valuationAt ≤ application.decisionAt

/-- The computed output existed by the decision boundary. -/
def OutputAvailable (application : HedgeScaleApplication) : Prop :=
  application.outputGeneratedAt ≤ application.decisionAt

/-- Current and hedge risks must be comparable risk quantities, while the
    registered control input is a whole-percent quantity. -/
def UnitsValid (application : HedgeScaleApplication) : Prop :=
  application.currentRisk.unit = application.hedgeRisk.unit ∧
    (application.currentRisk.unit = .usdRisk ∨
      application.currentRisk.unit = .eurRisk) ∧
        application.riskPercentage.unit = .percent

/-- The numerator and denominator risks refer to the same valuation boundary. -/
def ValuationAligned (application : HedgeScaleApplication) : Prop :=
  application.currentRisk.valuationAt = application.hedgeRisk.valuationAt

/-- The two risk quantities were produced by the same model identity and
    version. -/
def ModelAligned (application : HedgeScaleApplication) : Prop :=
  application.currentRisk.modelId = application.hedgeRisk.modelId ∧
    application.currentRisk.modelVersion =
      application.hedgeRisk.modelVersion

/-- Both the economic hedge denominator and the represented rational denominator
    are nonzero. -/
def DomainValid (application : HedgeScaleApplication) : Prop :=
  application.hedgeRisk.value ≠ 0 ∧
    application.claimedDenominator ≠ 0

/-- Inputs and output carry nonempty artifact identities. -/
def ArtifactsBound (application : HedgeScaleApplication) : Prop :=
  NonEmptyString application.currentRisk.artifactHash ∧
    NonEmptyString application.hedgeRisk.artifactHash ∧
      NonEmptyString application.riskPercentage.artifactHash ∧
        NonEmptyString application.outputArtifactHash

/-- Exact cross-multiplication binds the claimed rational result to the exact
    input values without trusting floating-point division. -/
def ResultBound (application : HedgeScaleApplication) : Prop :=
  application.claimedNumerator *
      (application.hedgeRisk.value * 100) =
    (-application.currentRisk.value * application.riskPercentage.value) *
      application.claimedDenominator

/-- Formula correctness and formula-application correctness are separate. A
    valid application must discharge every causal, dimensional, model, domain,
    artifact, and result-binding obligation. -/
structure Valid
    (application : HedgeScaleApplication)
    (definition : FormulaDefinition) : Prop where
  definitionMatched : application.DefinitionMatched definition
  definitionAvailable : application.DefinitionAvailable definition
  inputsAvailable : application.InputsAvailable
  valuationsNotFuture : application.ValuationsNotFuture
  outputAvailable : application.OutputAvailable
  unitsValid : application.UnitsValid
  valuationAligned : application.ValuationAligned
  modelAligned : application.ModelAligned
  domainValid : application.DomainValid
  artifactsBound : application.ArtifactsBound
  resultBound : application.ResultBound

end HedgeScaleApplication

/-- Proof-carrying formula application. -/
structure FormulaApplicationCertificate where
  definition : FormulaDefinition
  application : HedgeScaleApplication
  valid : application.Valid definition

namespace FormulaApplicationCertificate

theorem formula_was_preregistered
    (certificate : FormulaApplicationCertificate) :
    certificate.application.DefinitionAvailable certificate.definition :=
  certificate.valid.definitionAvailable

theorem temporal_inputs_are_available
    (certificate : FormulaApplicationCertificate) :
    certificate.application.InputsAvailable :=
  certificate.valid.inputsAvailable

theorem units_are_compatible
    (certificate : FormulaApplicationCertificate) :
    certificate.application.UnitsValid :=
  certificate.valid.unitsValid

theorem output_is_bound_to_exact_inputs
    (certificate : FormulaApplicationCertificate) :
    certificate.application.ResultBound :=
  certificate.valid.resultBound

end FormulaApplicationCertificate

end LeanFinance.Formula
