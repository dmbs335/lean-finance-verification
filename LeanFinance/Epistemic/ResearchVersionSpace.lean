import LeanFinance.Epistemic.VersionSpace
import LeanFinance.Core

namespace LeanFinance.Epistemic

universe uData uModel uSearch uExecution uUniverse uWorld uEvidence

/-- One complete financial-research world. The five coordinates separate data
    vintage, model version, adaptive search history, execution semantics, and
    universe/security-resolution state. -/
structure ResearchWorld
    (Data : Type uData)
    (Model : Type uModel)
    (Search : Type uSearch)
    (Execution : Type uExecution)
    (Universe : Type uUniverse) where
  dataState : Data
  modelState : Model
  searchState : Search
  executionState : Execution
  universeState : Universe
  deriving Repr

/-- Evidence and time determine which complete research worlds remain
    admissible. Coupling constraints can express relationships that do not
    factor by coordinate. -/
structure ResearchVersionSpace
    (World : Type uWorld)
    (Evidence : Type uEvidence) where
  admissible : Timestamp → Evidence → World → Prop

namespace ResearchVersionSpace

/-- Stronger evidence refines weaker evidence when every world surviving the
    stronger evidence also survived the weaker evidence. -/
def EvidenceRefines
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (stronger weaker : Evidence) : Prop :=
  ∀ world,
    space.admissible cutoff stronger world →
      space.admissible cutoff weaker world

theorem evidence_refines_refl
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (evidence : Evidence) :
    space.EvidenceRefines cutoff evidence evidence := by
  intro world allowed
  exact allowed

theorem evidence_refines_trans
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (stronger middle weaker : Evidence)
    (strongerToMiddle :
      space.EvidenceRefines cutoff stronger middle)
    (middleToWeaker :
      space.EvidenceRefines cutoff middle weaker) :
    space.EvidenceRefines cutoff stronger weaker := by
  intro world allowed
  exact middleToWeaker world
    (strongerToMiddle world allowed)

/-- A lower metric bound is valid in every admissible world. -/
def LowerBound
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (evidence : Evidence)
    (metric : World → Int)
    (candidate : Int) : Prop :=
  ∀ world,
    space.admissible cutoff evidence world →
      candidate ≤ metric world

/-- An upper metric bound is valid in every admissible world. -/
def UpperBound
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (evidence : Evidence)
    (metric : World → Int)
    (candidate : Int) : Prop :=
  ∀ world,
    space.admissible cutoff evidence world →
      metric world ≤ candidate

/-- The largest valid lower bound, carried as a proof rather than assumed to
    exist for every abstract space. -/
def GreatestLowerBound
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (evidence : Evidence)
    (metric : World → Int)
    (candidate : Int) : Prop :=
  space.LowerBound cutoff evidence metric candidate ∧
    ∀ other,
      space.LowerBound cutoff evidence metric other →
        other ≤ candidate

/-- The smallest valid upper bound. -/
def LeastUpperBound
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (evidence : Evidence)
    (metric : World → Int)
    (candidate : Int) : Prop :=
  space.UpperBound cutoff evidence metric candidate ∧
    ∀ other,
      space.UpperBound cutoff evidence metric other →
        candidate ≤ other

/-- An exact certifiable metric interval for one evidence state. -/
structure ExactMetricRange
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (evidence : Evidence)
    (metric : World → Int) where
  lower : Int
  upper : Int
  ordered : lower ≤ upper
  lowerIsGreatest :
    space.GreatestLowerBound cutoff evidence metric lower
  upperIsLeast :
    space.LeastUpperBound cutoff evidence metric upper

/-- The inner range is nested inside the outer range. -/
def RangeNarrows
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    {space : ResearchVersionSpace World Evidence}
    {cutoff : Timestamp}
    {outerEvidence innerEvidence : Evidence}
    {metric : World → Int}
    (outer : ExactMetricRange space cutoff outerEvidence metric)
    (inner : ExactMetricRange space cutoff innerEvidence metric) : Prop :=
  outer.lower ≤ inner.lower ∧
    inner.upper ≤ outer.upper

/-- Any bound valid for a larger world family remains valid after evidence
    restricts that family. -/
theorem lower_bound_preserved_under_refinement
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (stronger weaker : Evidence)
    (metric : World → Int)
    (candidate : Int)
    (refines : space.EvidenceRefines cutoff stronger weaker)
    (valid : space.LowerBound cutoff weaker metric candidate) :
    space.LowerBound cutoff stronger metric candidate := by
  intro world allowed
  exact valid world (refines world allowed)

theorem upper_bound_preserved_under_refinement
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (stronger weaker : Evidence)
    (metric : World → Int)
    (candidate : Int)
    (refines : space.EvidenceRefines cutoff stronger weaker)
    (valid : space.UpperBound cutoff weaker metric candidate) :
    space.UpperBound cutoff stronger metric candidate := by
  intro world allowed
  exact valid world (refines world allowed)

/-- Exact certifiable ranges are antitone in the admissible world family:
    stronger evidence can only move the lower endpoint upward and the upper
    endpoint downward. -/
theorem exact_range_narrows_under_refinement
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (stronger weaker : Evidence)
    (metric : World → Int)
    (refines : space.EvidenceRefines cutoff stronger weaker)
    (outer : ExactMetricRange space cutoff weaker metric)
    (inner : ExactMetricRange space cutoff stronger metric) :
    RangeNarrows outer inner := by
  have oldLowerStillValid :
      space.LowerBound cutoff stronger metric outer.lower :=
    space.lower_bound_preserved_under_refinement
      cutoff stronger weaker metric outer.lower refines
      outer.lowerIsGreatest.1
  have oldUpperStillValid :
      space.UpperBound cutoff stronger metric outer.upper :=
    space.upper_bound_preserved_under_refinement
      cutoff stronger weaker metric outer.upper refines
      outer.upperIsLeast.1
  exact ⟨
    inner.lowerIsGreatest.2 outer.lower oldLowerStillValid,
    inner.upperIsLeast.2 outer.upper oldUpperStillValid⟩

/-- The metric is point-identified when every two admissible worlds agree. -/
def MetricIdentified
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (evidence : Evidence)
    (metric : World → Int) : Prop :=
  ∀ left right,
    space.admissible cutoff evidence left →
      space.admissible cutoff evidence right →
        metric left = metric right

/-- When at least one world survives and all surviving worlds agree, an exact
    metric range collapses to a point. -/
theorem exact_range_collapses_of_identification
    {World : Type uWorld}
    {Evidence : Type uEvidence}
    (space : ResearchVersionSpace World Evidence)
    (cutoff : Timestamp)
    (evidence : Evidence)
    (metric : World → Int)
    (exactRange : ExactMetricRange space cutoff evidence metric)
    (survives : ∃ world, space.admissible cutoff evidence world)
    (identified : space.MetricIdentified cutoff evidence metric) :
    exactRange.lower = exactRange.upper := by
  rcases survives with ⟨world, worldAllowed⟩
  have metricIsLower :
      space.LowerBound cutoff evidence metric (metric world) := by
    intro other otherAllowed
    exact le_of_eq
      (identified world other worldAllowed otherAllowed)
  have metricIsUpper :
      space.UpperBound cutoff evidence metric (metric world) := by
    intro other otherAllowed
    exact le_of_eq
      (identified other world otherAllowed worldAllowed)
  have metricLeLower : metric world ≤ exactRange.lower :=
    exactRange.lowerIsGreatest.2 (metric world) metricIsLower
  have upperLeMetric : exactRange.upper ≤ metric world :=
    exactRange.upperIsLeast.2 (metric world) metricIsUpper
  exact le_antisymm exactRange.ordered
    (le_trans upperLeMetric metricLeLower)

end ResearchVersionSpace

/-- A factorized policy exposes the five main uncertainty coordinates while
    retaining a coupling predicate for interactions such as future data used by
    adaptive search or a model tied to a revised universe. -/
structure FactorizedResearchPolicy
    (Data : Type uData)
    (Model : Type uModel)
    (Search : Type uSearch)
    (Execution : Type uExecution)
    (Universe : Type uUniverse)
    (Evidence : Type uEvidence) where
  dataAdmissible : Timestamp → Evidence → Data → Prop
  modelAdmissible : Timestamp → Evidence → Model → Prop
  searchAdmissible : Timestamp → Evidence → Search → Prop
  executionAdmissible : Timestamp → Evidence → Execution → Prop
  universeAdmissible : Timestamp → Evidence → Universe → Prop
  couplingAdmissible :
    Timestamp → Evidence →
      ResearchWorld Data Model Search Execution Universe → Prop

namespace FactorizedResearchPolicy

/-- Convert coordinate predicates and coupling constraints into the common
    admissible-world calculus. -/
def toVersionSpace
    {Data : Type uData}
    {Model : Type uModel}
    {Search : Type uSearch}
    {Execution : Type uExecution}
    {Universe : Type uUniverse}
    {Evidence : Type uEvidence}
    (policy :
      FactorizedResearchPolicy
        Data Model Search Execution Universe Evidence) :
    ResearchVersionSpace
      (ResearchWorld Data Model Search Execution Universe)
      Evidence :=
  { admissible := fun cutoff evidence world =>
      policy.dataAdmissible cutoff evidence world.dataState ∧
        policy.modelAdmissible cutoff evidence world.modelState ∧
          policy.searchAdmissible cutoff evidence world.searchState ∧
            policy.executionAdmissible cutoff evidence
              world.executionState ∧
              policy.universeAdmissible cutoff evidence
                world.universeState ∧
                policy.couplingAdmissible cutoff evidence world }

/-- Componentwise evidence refinement plus coupling refinement is sufficient to
    refine the complete research-world version space. -/
theorem evidence_refines_of_componentwise_refinement
    {Data : Type uData}
    {Model : Type uModel}
    {Search : Type uSearch}
    {Execution : Type uExecution}
    {Universe : Type uUniverse}
    {Evidence : Type uEvidence}
    (policy :
      FactorizedResearchPolicy
        Data Model Search Execution Universe Evidence)
    (cutoff : Timestamp)
    (stronger weaker : Evidence)
    (dataRefines : ∀ state,
      policy.dataAdmissible cutoff stronger state →
        policy.dataAdmissible cutoff weaker state)
    (modelRefines : ∀ state,
      policy.modelAdmissible cutoff stronger state →
        policy.modelAdmissible cutoff weaker state)
    (searchRefines : ∀ state,
      policy.searchAdmissible cutoff stronger state →
        policy.searchAdmissible cutoff weaker state)
    (executionRefines : ∀ state,
      policy.executionAdmissible cutoff stronger state →
        policy.executionAdmissible cutoff weaker state)
    (universeRefines : ∀ state,
      policy.universeAdmissible cutoff stronger state →
        policy.universeAdmissible cutoff weaker state)
    (couplingRefines : ∀ world,
      policy.couplingAdmissible cutoff stronger world →
        policy.couplingAdmissible cutoff weaker world) :
    policy.toVersionSpace.EvidenceRefines cutoff stronger weaker := by
  intro world allowed
  exact ⟨dataRefines world.dataState allowed.1,
    ⟨modelRefines world.modelState allowed.2.1,
      ⟨searchRefines world.searchState allowed.2.2.1,
        ⟨executionRefines world.executionState allowed.2.2.2.1,
          ⟨universeRefines world.universeState allowed.2.2.2.2.1,
            couplingRefines world allowed.2.2.2.2.2⟩⟩⟩⟩⟩

end FactorizedResearchPolicy

end LeanFinance.Epistemic
