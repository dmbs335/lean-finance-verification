import LeanFinance.Types
import LeanFinance.Inference.Identification

namespace LeanFinance.StrategyEcology

universe u v

/-- One target-strategy row of the directed interaction kernel. -/
abbrev KernelRow (Source : Type u) := Source → Scalar

def zeroRow {Source : Type u} : KernelRow Source :=
  fun _ => 0

def addRow {Source : Type u}
    (left right : KernelRow Source) : KernelRow Source :=
  fun source => left source + right source

/-- Abstract linear first-stage moment map. A nonzero null direction is the
    constructive content needed for the rank-deficiency result. -/
structure LinearObservation (Source : Type u) (Instrument : Type v) where
  observe : KernelRow Source → Instrument → Scalar
  mapZero : ∀ instrument,
    observe (zeroRow (Source := Source)) instrument = 0
  mapAdd : ∀ left right instrument,
    observe (addRow left right) instrument =
      observe left instrument + observe right instrument

def NullDirection
    {Source : Type u}
    {Instrument : Type v}
    (system : LinearObservation Source Instrument)
    (direction : KernelRow Source) : Prop :=
  ∀ instrument, system.observe direction instrument = 0

theorem nullDirection_preserves_observation
    {Source : Type u}
    {Instrument : Type v}
    (system : LinearObservation Source Instrument)
    (row direction : KernelRow Source)
    (nullDirection : NullDirection system direction) :
    system.observe (addRow row direction) = system.observe row := by
  funext instrument
  rw [system.mapAdd]
  rw [nullDirection instrument]
  simp

def coordinate
    {Source : Type u}
    (source : Source)
    (row : KernelRow Source) : Scalar :=
  row source

theorem zero_observationallyEquivalent_nullDirection
    {Source : Type u}
    {Instrument : Type v}
    (system : LinearObservation Source Instrument)
    (direction : KernelRow Source)
    (nullDirection : NullDirection system direction) :
    Inference.ObservationallyEquivalent
      system.observe (zeroRow (Source := Source)) direction := by
  funext instrument
  rw [system.mapZero]
  rw [nullDirection instrument]

/-- If the first-stage map has a null direction that changes one source
    coordinate, that interaction coordinate is not point identified. This is a
    constructive rank-deficiency certificate. -/
theorem coordinate_not_identified_of_nullDirection
    {Source : Type u}
    {Instrument : Type v}
    (system : LinearObservation Source Instrument)
    (direction : KernelRow Source)
    (source : Source)
    (nullDirection : NullDirection system direction)
    (nonzeroCoordinate : direction source ≠ 0) :
    ¬ Inference.Identified system.observe (coordinate source) := by
  apply Inference.not_identified_of_counterexample
    system.observe
    (coordinate source)
    (zeroRow (Source := Source))
    direction
  · exact zero_observationallyEquivalent_nullDirection
      system direction nullDirection
  · intro equalCoordinate
    apply nonzeroCoordinate
    change (0 : Scalar) = direction source at equalCoordinate
    exact equalCoordinate.symm

/-- Scalar reduced-form moment equation used by a local IV edge estimate. -/
def FitsMoments
    (firstStage reducedForm effect : Scalar) : Prop :=
  reducedForm = effect * firstStage

/-- Relevance is stated as the exact cancellation property needed for unique
    identification, avoiding an unproved statistical interpretation. -/
def Relevant (firstStage : Scalar) : Prop :=
  ∀ left right : Scalar,
    left * firstStage = right * firstStage → left = right

theorem effect_unique_of_relevance
    {firstStage reducedForm left right : Scalar}
    (relevance : Relevant firstStage)
    (leftFits : FitsMoments firstStage reducedForm left)
    (rightFits : FitsMoments firstStage reducedForm right) :
    left = right := by
  apply relevance left right
  calc
    left * firstStage = reducedForm := leftFits.symm
    _ = right * firstStage := rightFits

theorem zero_firstStage_zero_reducedForm_fits_every_effect
    (effect : Scalar) :
    FitsMoments 0 0 effect := by
  simp [FitsMoments]

/-- Proof object for the scalar LP-IV moment equation and its uniqueness
    condition. Statistical exogeneity and exclusion are carried separately by
    the causal edge certificate. -/
structure ScalarIVCertificate where
  firstStage : Scalar
  reducedForm : Scalar
  effect : Scalar
  momentEquation : FitsMoments firstStage reducedForm effect
  relevance : Relevant firstStage

theorem ScalarIVCertificate.effectUnique
    (certificate : ScalarIVCertificate)
    (alternative : Scalar)
    (alternativeFits :
      FitsMoments certificate.firstStage
        certificate.reducedForm alternative) :
    alternative = certificate.effect :=
  effect_unique_of_relevance
    certificate.relevance
    alternativeFits
    certificate.momentEquation

end LeanFinance.StrategyEcology
