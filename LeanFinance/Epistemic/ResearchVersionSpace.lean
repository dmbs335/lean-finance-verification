import LeanFinance.Core

namespace LeanFinance.Epistemic

/-- One complete hidden financial-research world. The coordinates separate
    sources of uncertainty that are often collapsed into one backtest number. -/
structure ResearchWorld where
  dataVintage : Nat
  modelVersion : Nat
  searchHistory : Nat
  executionSemantics : Nat
  universeVersion : Nat
  deriving Repr, DecidableEq

/-- A metric can depend on every research-world coordinate and their
    interactions. -/
def worldMetric
    (metric : ResearchWorld → Int)
    (world : ResearchWorld) : Int :=
  metric world

/-- Evidence at one cutoff determines the admissible family of complete research
    worlds. -/
structure ResearchVersionSpace where
  allows : ResearchWorld → Prop

namespace ResearchVersionSpace

/-- Stronger evidence refines weaker evidence when every world surviving the
    stronger evidence also survived the weaker evidence. -/
def EvidenceRefines
    (stronger weaker : ResearchVersionSpace) : Prop :=
  ∀ world,
    stronger.allows world → weaker.allows world

theorem evidence_refinement_refl
    (space : ResearchVersionSpace) :
    space.EvidenceRefines space := by
  intro world allowed
  exact allowed

theorem evidence_refinement_trans
    (strong middle weak : ResearchVersionSpace)
    (strongMiddle : strong.EvidenceRefines middle)
    (middleWeak : middle.EvidenceRefines weak) :
    strong.EvidenceRefines weak := by
  intro world allowed
  exact middleWeak world (strongMiddle world allowed)

/-- Exact lower and upper metric endpoints over an admissible world family.

    `greatestLower` and `leastUpper` quantify over candidate bounds. This is the
    actual GLB/LUB contract; quantifying only over worlds would incorrectly force
    every exact range to collapse to a point. -/
structure ExactMetricRange
    (space : ResearchVersionSpace)
    (metric : ResearchWorld → Int) where
  lower : Int
  upper : Int
  ordered : lower ≤ upper
  lowerBound :
    ∀ world,
      space.allows world → lower ≤ metric world
  upperBound :
    ∀ world,
      space.allows world → metric world ≤ upper
  greatestLower :
    ∀ candidate,
      (∀ world, space.allows world → candidate ≤ metric world) →
        candidate ≤ lower
  leastUpper :
    ∀ candidate,
      (∀ world, space.allows world → metric world ≤ candidate) →
        upper ≤ candidate

/-- Restricting admissible worlds cannot lower the exact lower endpoint. -/
theorem exact_lower_bound_monotone_under_refinement
    (strong weak : ResearchVersionSpace)
    (metric : ResearchWorld → Int)
    (refinement : strong.EvidenceRefines weak)
    (weakRange : ExactMetricRange weak metric)
    (strongRange : ExactMetricRange strong metric) :
    weakRange.lower ≤ strongRange.lower := by
  apply strongRange.greatestLower weakRange.lower
  intro world strongAllowed
  exact weakRange.lowerBound world
    (refinement world strongAllowed)

/-- Restricting admissible worlds cannot raise the exact upper endpoint. -/
theorem exact_upper_bound_monotone_under_refinement
    (strong weak : ResearchVersionSpace)
    (metric : ResearchWorld → Int)
    (refinement : strong.EvidenceRefines weak)
    (weakRange : ExactMetricRange weak metric)
    (strongRange : ExactMetricRange strong metric) :
    strongRange.upper ≤ weakRange.upper := by
  apply strongRange.leastUpper weakRange.upper
  intro world strongAllowed
  exact weakRange.upperBound world
    (refinement world strongAllowed)

/-- Exact certifiable metric ranges are nested under stronger evidence. -/
theorem exact_range_narrows_under_refinement
    (strong weak : ResearchVersionSpace)
    (metric : ResearchWorld → Int)
    (refinement : strong.EvidenceRefines weak)
    (weakRange : ExactMetricRange weak metric)
    (strongRange : ExactMetricRange strong metric) :
    weakRange.lower ≤ strongRange.lower ∧
      strongRange.upper ≤ weakRange.upper :=
  ⟨exact_lower_bound_monotone_under_refinement
      strong weak metric refinement weakRange strongRange,
    exact_upper_bound_monotone_under_refinement
      strong weak metric refinement weakRange strongRange⟩

/-- If every surviving world has one identified metric value, the exact range
    collapses to that point. The proof uses the exact-range ordering invariant
    and the least-upper-bound property explicitly. -/
theorem exact_range_collapses_of_identification
    (space : ResearchVersionSpace)
    (metric : ResearchWorld → Int)
    (exactRange : ExactMetricRange space metric)
    (_existsAllowed : ∃ world, space.allows world)
    (identified :
      ∀ world,
        space.allows world → metric world = exactRange.lower) :
    exactRange.lower = exactRange.upper := by
  have upperLeLower : exactRange.upper ≤ exactRange.lower := by
    apply exactRange.leastUpper exactRange.lower
    intro world allowed
    exact le_of_eq (identified world allowed)
  exact le_antisymm exactRange.ordered upperLeLower

end ResearchVersionSpace

end LeanFinance.Epistemic
