import LeanFinance.Epistemic.ResearchVersionSpace

namespace LeanFinance.Epistemic.ResearchVersionSpaceExample

open LeanFinance.Epistemic

/-- Controlled metric with five main effects and two interactions. -/
def controlledMetric (world : ResearchWorld) : Int :=
  20
    + (if world.dataVintage = 1 then 40 else 0)
    + (if world.modelVersion = 1 then 10 else 0)
    + (if world.searchHistory = 1 then 30 else 0)
    + (if world.executionSemantics = 1 then 15 else 0)
    + (if world.universeVersion = 1 then 5 else 0)
    + (if world.dataVintage = 1 ∧ world.searchHistory = 1 then 25 else 0)
    + (if world.executionSemantics = 1 ∧ world.universeVersion = 1
       then 5 else 0)

def weakEvidence : ResearchVersionSpace :=
  { allows := fun world =>
      world.dataVintage ≤ 1 ∧
        world.modelVersion ≤ 1 ∧
          world.searchHistory ≤ 1 ∧
            world.executionSemantics ≤ 1 ∧
              world.universeVersion ≤ 1 }

def strongEvidence : ResearchVersionSpace :=
  { allows := fun world =>
      world.dataVintage = 0 ∧
        world.modelVersion ≤ 1 ∧
          world.searchHistory = 0 ∧
            world.executionSemantics ≤ 1 ∧
              world.universeVersion ≤ 1 }

def identifiedEvidence : ResearchVersionSpace :=
  { allows := fun world =>
      world.dataVintage = 0 ∧
        world.modelVersion = 0 ∧
          world.searchHistory = 0 ∧
            world.executionSemantics = 0 ∧
              world.universeVersion = 0 }

def baselineWorld : ResearchWorld :=
  { dataVintage := 0
    modelVersion := 0
    searchHistory := 0
    executionSemantics := 0
    universeVersion := 0 }

def allAlternativeWorld : ResearchWorld :=
  { dataVintage := 1
    modelVersion := 1
    searchHistory := 1
    executionSemantics := 1
    universeVersion := 1 }

def strongUpperWorld : ResearchWorld :=
  { dataVintage := 0
    modelVersion := 1
    searchHistory := 0
    executionSemantics := 1
    universeVersion := 1 }

theorem strong_refines_weak :
    strongEvidence.EvidenceRefines weakEvidence := by
  intro world allowed
  rcases allowed with
    ⟨dataZero, modelBound, searchZero, executionBound, universeBound⟩
  exact ⟨by omega, modelBound, by omega, executionBound, universeBound⟩

def weakRange :
    ResearchVersionSpace.ExactMetricRange weakEvidence controlledMetric :=
  { lower := 20
    upper := 150
    ordered := by decide
    lowerBound := by
      intro world _allowed
      simp only [controlledMetric]
      split_ifs <;> omega
    upperBound := by
      intro world _allowed
      simp only [controlledMetric]
      split_ifs <;> omega
    greatestLower := by
      intro candidate candidateLower
      have witness := candidateLower baselineWorld (by decide)
      simpa [controlledMetric, baselineWorld] using witness
    leastUpper := by
      intro candidate candidateUpper
      have witness := candidateUpper allAlternativeWorld (by decide)
      simpa [controlledMetric, allAlternativeWorld] using witness }

def strongRange :
    ResearchVersionSpace.ExactMetricRange strongEvidence controlledMetric :=
  { lower := 20
    upper := 55
    ordered := by decide
    lowerBound := by
      intro world _allowed
      simp only [controlledMetric]
      split_ifs <;> omega
    upperBound := by
      intro world allowed
      rcases allowed with
        ⟨dataZero, _modelBound, searchZero, _executionBound,
          _universeBound⟩
      simp only [controlledMetric, dataZero, searchZero]
      split_ifs <;> omega
    greatestLower := by
      intro candidate candidateLower
      have witness := candidateLower baselineWorld (by decide)
      simpa [controlledMetric, baselineWorld] using witness
    leastUpper := by
      intro candidate candidateUpper
      have witness := candidateUpper strongUpperWorld (by decide)
      simpa [controlledMetric, strongUpperWorld] using witness }

def identifiedRange :
    ResearchVersionSpace.ExactMetricRange
      identifiedEvidence controlledMetric :=
  { lower := 20
    upper := 20
    ordered := by decide
    lowerBound := by
      intro world allowed
      rcases allowed with ⟨hData, hModel, hSearch, hExecution, hUniverse⟩
      simp [controlledMetric, hData, hModel, hSearch, hExecution, hUniverse]
    upperBound := by
      intro world allowed
      rcases allowed with ⟨hData, hModel, hSearch, hExecution, hUniverse⟩
      simp [controlledMetric, hData, hModel, hSearch, hExecution, hUniverse]
    greatestLower := by
      intro candidate candidateLower
      have witness := candidateLower baselineWorld (by decide)
      simpa [controlledMetric, baselineWorld] using witness
    leastUpper := by
      intro candidate candidateUpper
      have witness := candidateUpper baselineWorld (by decide)
      simpa [controlledMetric, baselineWorld] using witness }

theorem stronger_evidence_narrows_the_controlled_range :
    weakRange.lower ≤ strongRange.lower ∧
      strongRange.upper ≤ weakRange.upper :=
  ResearchVersionSpace.exact_range_narrows_under_refinement
    strongEvidence weakEvidence controlledMetric
    strong_refines_weak weakRange strongRange

theorem identified_worlds_have_baseline_metric :
    ∀ world,
      identifiedEvidence.allows world →
        controlledMetric world = identifiedRange.lower := by
  intro world allowed
  rcases allowed with ⟨hData, hModel, hSearch, hExecution, hUniverse⟩
  simp [controlledMetric, identifiedRange, hData, hModel, hSearch,
    hExecution, hUniverse]

theorem identification_collapses_range :
    identifiedRange.lower = identifiedRange.upper :=
  ResearchVersionSpace.exact_range_collapses_of_identification
    identifiedEvidence controlledMetric identifiedRange
    ⟨baselineWorld, by decide⟩
    identified_worlds_have_baseline_metric

end LeanFinance.Epistemic.ResearchVersionSpaceExample
