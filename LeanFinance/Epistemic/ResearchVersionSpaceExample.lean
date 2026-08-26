import LeanFinance.Epistemic.ResearchVersionSpace

namespace LeanFinance.Epistemic.ResearchVersionSpaceExample

open LeanFinance.Epistemic

/-- A compact controlled family. The executable benchmark expands the same five
    dimensions to the full 2^5 Cartesian product. -/
inductive ControlledWorld where
  | baseline
  | latestData
  | latestModel
  | adaptiveSearch
  | optimisticExecution
  | survivorUniverse
  | allOptimistic
  deriving Repr, DecidableEq

structure ControlledEvidence where
  dataReceipt : Bool
  modelReceipt : Bool
  searchLedger : Bool
  executionReceipt : Bool
  universeSnapshot : Bool
  deriving Repr, DecidableEq

def noEvidence : ControlledEvidence :=
  { dataReceipt := false
    modelReceipt := false
    searchLedger := false
    executionReceipt := false
    universeSnapshot := false }

def fullEvidence : ControlledEvidence :=
  { dataReceipt := true
    modelReceipt := true
    searchLedger := true
    executionReceipt := true
    universeSnapshot := true }

def controlledAdmissible
    (evidence : ControlledEvidence) : ControlledWorld → Prop
  | .baseline => True
  | .latestData => evidence.dataReceipt = false
  | .latestModel => evidence.modelReceipt = false
  | .adaptiveSearch => evidence.searchLedger = false
  | .optimisticExecution => evidence.executionReceipt = false
  | .survivorUniverse => evidence.universeSnapshot = false
  | .allOptimistic =>
      evidence.dataReceipt = false ∧
        evidence.modelReceipt = false ∧
          evidence.searchLedger = false ∧
            evidence.executionReceipt = false ∧
              evidence.universeSnapshot = false

def controlledSpace :
    ResearchVersionSpace ControlledWorld ControlledEvidence :=
  { admissible := fun _cutoff evidence world =>
      controlledAdmissible evidence world }

def controlledMetric : ControlledWorld → Int
  | .baseline => 20
  | .latestData => 60
  | .latestModel => 30
  | .adaptiveSearch => 50
  | .optimisticExecution => 35
  | .survivorUniverse => 25
  | .allOptimistic => 150

/-- Optional projection showing how each controlled world occupies the five
    uncertainty coordinates. -/
def components : ControlledWorld →
    ResearchWorld Bool Bool Bool Bool Bool
  | .baseline => ⟨false, false, false, false, false⟩
  | .latestData => ⟨true, false, false, false, false⟩
  | .latestModel => ⟨false, true, false, false, false⟩
  | .adaptiveSearch => ⟨false, false, true, false, false⟩
  | .optimisticExecution => ⟨false, false, false, true, false⟩
  | .survivorUniverse => ⟨false, false, false, false, true⟩
  | .allOptimistic => ⟨true, true, true, true, true⟩

def noEvidenceRange :
    ResearchVersionSpace.ExactMetricRange
      controlledSpace 100 noEvidence controlledMetric :=
  { lower := 20
    upper := 150
    ordered := by decide
    lowerIsGreatest := by
      constructor
      · intro world _allowed
        cases world <;> decide
      · intro candidate valid
        have atBaseline := valid .baseline (by
          simp [controlledSpace, controlledAdmissible])
        simpa [controlledMetric] using atBaseline
    upperIsLeast := by
      constructor
      · intro world _allowed
        cases world <;> decide
      · intro candidate valid
        have atOptimistic := valid .allOptimistic (by
          simp [controlledSpace, controlledAdmissible, noEvidence])
        simpa [controlledMetric] using atOptimistic }

def fullEvidenceRange :
    ResearchVersionSpace.ExactMetricRange
      controlledSpace 100 fullEvidence controlledMetric :=
  { lower := 20
    upper := 20
    ordered := by decide
    lowerIsGreatest := by
      constructor
      · intro world allowed
        cases world <;>
          simp_all [controlledSpace, controlledAdmissible,
            fullEvidence, controlledMetric]
      · intro candidate valid
        have atBaseline := valid .baseline (by
          simp [controlledSpace, controlledAdmissible])
        simpa [controlledMetric] using atBaseline
    upperIsLeast := by
      constructor
      · intro world allowed
        cases world <;>
          simp_all [controlledSpace, controlledAdmissible,
            fullEvidence, controlledMetric]
      · intro candidate valid
        have atBaseline := valid .baseline (by
          simp [controlledSpace, controlledAdmissible])
        simpa [controlledMetric] using atBaseline }

theorem full_evidence_refines_none :
    controlledSpace.EvidenceRefines 100 fullEvidence noEvidence := by
  intro world allowed
  cases world <;>
    simp_all [controlledSpace, controlledAdmissible,
      fullEvidence, noEvidence]

theorem full_range_is_nested :
    ResearchVersionSpace.RangeNarrows
      noEvidenceRange fullEvidenceRange :=
  controlledSpace.exact_range_narrows_under_refinement
    100 fullEvidence noEvidence controlledMetric
    full_evidence_refines_none noEvidenceRange fullEvidenceRange

theorem full_evidence_identifies_metric :
    controlledSpace.MetricIdentified
      100 fullEvidence controlledMetric := by
  intro left right leftAllowed rightAllowed
  cases left <;> cases right <;>
    simp_all [controlledSpace, controlledAdmissible,
      fullEvidence, controlledMetric]

theorem full_exact_range_collapses :
    fullEvidenceRange.lower = fullEvidenceRange.upper :=
  controlledSpace.exact_range_collapses_of_identification
    100 fullEvidence controlledMetric fullEvidenceRange
    ⟨.baseline, by
      simp [controlledSpace, controlledAdmissible]⟩
    full_evidence_identifies_metric

theorem uncertainty_width_falls_from_one_hundred_thirty_to_zero :
    noEvidenceRange.upper - noEvidenceRange.lower = 130 ∧
      fullEvidenceRange.upper - fullEvidenceRange.lower = 0 := by
  decide

end LeanFinance.Epistemic.ResearchVersionSpaceExample
