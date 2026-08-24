import LeanFinance.Core

namespace LeanFinance.Alpha

/-- A research process is separated from the realized return it produces.
    The same observed return may have different evidential validity depending
    on the admissible hidden histories and models. -/
structure EvidenceState where
  historySpaceSize : Nat
  modelSpaceSize : Nat
  evidenceCost : Nat
  deriving Repr

/-- Conventional realized alpha is represented as an integer-scaled excess
    return in the core research model. -/
def RealizedAlpha := Int

/-- A conservative certifiable alpha interval. The lower bound is the alpha
    surviving all histories and models represented by the evidence state. -/
structure CertifiableAlpha where
  lowerBound : RealizedAlpha
  upperBound : RealizedAlpha
  state : EvidenceState
  deriving Repr

/-- More evidence can reduce the admissible uncertainty space. -/
def MoreInformative
    (strong weak : EvidenceState) : Prop :=
  strong.historySpaceSize ≤ weak.historySpaceSize ∧
  strong.modelSpaceSize ≤ weak.modelSpaceSize

/-- Evidence refinement cannot enlarge the admissible alpha interval when the
    represented history and model spaces shrink. -/
theorem refinement_reduces_uncertainty
    (strong weak : EvidenceState)
    (refinement : MoreInformative strong weak) :
    strong.historySpaceSize ≤ weak.historySpaceSize :=
  refinement.1

/-- A strategy with identical realized returns can have different
    certifiability because evidence states differ. -/
structure StrategyCertificate where
  strategyId : String
  realizedAlpha : RealizedAlpha
  certifiable : CertifiableAlpha

end LeanFinance.Alpha
