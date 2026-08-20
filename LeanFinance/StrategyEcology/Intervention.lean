import LeanFinance.Core

namespace LeanFinance.StrategyEcology

/-- The state required to distinguish pure scale from a mutation of the
    strategy genome. -/
structure StrategyState (Genome : Type) where
  genome : Genome
  riskBudget : Scalar
  deriving Repr

/-- A pure scale intervention changes risk budget while holding the strategy
    genome fixed. -/
def GenomeFixedScale
    {Genome : Type}
    (before after : StrategyState Genome)
    (delta : Scalar) : Prop :=
  after.genome = before.genome ∧
    after.riskBudget = before.riskBudget + delta

theorem genomeFixedScale_zero
    {Genome : Type}
    (state : StrategyState Genome) :
    GenomeFixedScale state state 0 := by
  simp [GenomeFixedScale]

/-- Sequential genome-fixed scale changes compose additively. -/
theorem genomeFixedScale_trans
    {Genome : Type}
    {before middle after : StrategyState Genome}
    {firstDelta secondDelta : Scalar}
    (first : GenomeFixedScale before middle firstDelta)
    (second : GenomeFixedScale middle after secondDelta) :
    GenomeFixedScale before after (firstDelta + secondDelta) := by
  constructor
  · exact second.1.trans first.1
  · rw [second.2, first.2]
    simp [add_assoc]

structure ScaleIntervention (Genome : Type) where
  before : StrategyState Genome
  after : StrategyState Genome
  delta : Scalar
  genomeFixed : GenomeFixedScale before after delta

theorem ScaleIntervention.preservesGenome
    {Genome : Type}
    (intervention : ScaleIntervention Genome) :
    intervention.after.genome = intervention.before.genome :=
  intervention.genomeFixed.1

theorem ScaleIntervention.shiftsRiskBudget
    {Genome : Type}
    (intervention : ScaleIntervention Genome) :
    intervention.after.riskBudget =
      intervention.before.riskBudget + intervention.delta :=
  intervention.genomeFixed.2

end LeanFinance.StrategyEcology
