import LeanFinance.Types

namespace LeanFinance.StrategyEcology

/-- The component of strategy fitness whose causal response is being studied. -/
inductive FitnessMetric where
  | netAlpha
  | certaintyEquivalent
  | capitalGrowth
  | expectedShortfall
  | drawdown
  | exitHazard
  | capacity
  deriving Repr, DecidableEq

/-- Capital, realized order flow, and strategy adoption are distinct treatments. -/
inductive TreatmentType where
  | capitalStock
  | orderFlow
  | adoption
  deriving Repr, DecidableEq

/-- Why a source-strategy shock occurred. Equal-sized flows with different
    provenance need not have equal causal effects. -/
inductive ShockProvenance where
  | benchmark
  | allocatorFlow
  | information
  | margin
  | regulation
  | issuerSupply
  | other
  deriving Repr, DecidableEq

/-- The conditions under which one directed strategy interaction is evaluated. -/
structure InteractionContext (Regime : Type) where
  horizon : Time
  regime : Regime
  metric : FitnessMetric
  treatment : TreatmentType
  provenance : ShockProvenance
  deriving Repr

/-- `effect target source context` is the local causal effect on the target
    strategy's selected fitness metric when the source treatment is increased. -/
structure CausalKernel (Strategy Regime : Type) where
  effect : Strategy → Strategy → InteractionContext Regime → Scalar

/-- Both strategies reduce the other's fitness in the selected context. -/
def Competition
    {Strategy Regime : Type}
    (kernel : CausalKernel Strategy Regime)
    (left right : Strategy)
    (context : InteractionContext Regime) : Prop :=
  kernel.effect left right context < 0 ∧
    kernel.effect right left context < 0

/-- Both strategies increase the other's fitness in the selected context. -/
def Mutualism
    {Strategy Regime : Type}
    (kernel : CausalKernel Strategy Regime)
    (left right : Strategy)
    (context : InteractionContext Regime) : Prop :=
  0 < kernel.effect left right context ∧
    0 < kernel.effect right left context

/-- The predator benefits from the prey population while the prey is harmed by
    the predator population. -/
def Predation
    {Strategy Regime : Type}
    (kernel : CausalKernel Strategy Regime)
    (predator prey : Strategy)
    (context : InteractionContext Regime) : Prop :=
  0 < kernel.effect predator prey context ∧
    kernel.effect prey predator context < 0

/-- The beneficiary gains while the neutral strategy is locally unaffected. -/
def Commensalism
    {Strategy Regime : Type}
    (kernel : CausalKernel Strategy Regime)
    (beneficiary neutral : Strategy)
    (context : InteractionContext Regime) : Prop :=
  0 < kernel.effect beneficiary neutral context ∧
    kernel.effect neutral beneficiary context = 0

/-- Negative own-density dependence: more capital in a strategy lowers its own
    selected fitness metric. -/
def Crowded
    {Strategy Regime : Type}
    (kernel : CausalKernel Strategy Regime)
    (strategy : Strategy)
    (context : InteractionContext Regime) : Prop :=
  kernel.effect strategy strategy context < 0

/-- A creator strategy raises the selected fitness of a harvester strategy. -/
def OpportunityCreatedBy
    {Strategy Regime : Type}
    (kernel : CausalKernel Strategy Regime)
    (harvester creator : Strategy)
    (context : InteractionContext Regime) : Prop :=
  0 < kernel.effect harvester creator context

theorem competition_symm
    {Strategy Regime : Type}
    {kernel : CausalKernel Strategy Regime}
    {left right : Strategy}
    {context : InteractionContext Regime}
    (interaction : Competition kernel left right context) :
    Competition kernel right left context :=
  ⟨interaction.2, interaction.1⟩

theorem mutualism_symm
    {Strategy Regime : Type}
    {kernel : CausalKernel Strategy Regime}
    {left right : Strategy}
    {context : InteractionContext Regime}
    (interaction : Mutualism kernel left right context) :
    Mutualism kernel right left context :=
  ⟨interaction.2, interaction.1⟩

theorem predation_asymmetric
    {Strategy Regime : Type}
    {kernel : CausalKernel Strategy Regime}
    {predator prey : Strategy}
    {context : InteractionContext Regime}
    (interaction : Predation kernel predator prey context) :
    ¬ Predation kernel prey predator context := by
  intro reverseInteraction
  exact lt_asymm interaction.1 reverseInteraction.2

theorem mutualism_not_competition
    {Strategy Regime : Type}
    {kernel : CausalKernel Strategy Regime}
    {left right : Strategy}
    {context : InteractionContext Regime}
    (interaction : Mutualism kernel left right context) :
    ¬ Competition kernel left right context := by
  intro competition
  exact lt_asymm interaction.1 competition.1

/-- A constructive witness that two contexts produce different effects rules
    out a single context-free scalar representing both effects. -/
theorem no_context_free_effect_of_context_dependence
    {Strategy Regime : Type}
    (kernel : CausalKernel Strategy Regime)
    (target source : Strategy)
    (first second : InteractionContext Regime)
    (different :
      kernel.effect target source first ≠
        kernel.effect target source second) :
    ¬ ∃ constant : Scalar,
      constant = kernel.effect target source first ∧
      constant = kernel.effect target source second := by
  intro representation
  rcases representation with ⟨constant, firstEq, secondEq⟩
  apply different
  exact firstEq.symm.trans secondEq

/-- Explicit channels used to distinguish partial-equilibrium impact from the
    general-equilibrium response of prices, liquidity, balance sheets, issuers,
    allocators, and target-strategy adaptation. -/
structure EffectChannels where
  direct : Scalar
  price : Scalar
  liquidity : Scalar
  funding : Scalar
  volatility : Scalar
  information : Scalar
  allocator : Scalar
  issuer : Scalar
  adaptation : Scalar
  deriving Repr

def feedbackEffect (channels : EffectChannels) : Scalar :=
  channels.price + channels.liquidity + channels.funding +
    channels.volatility + channels.information + channels.allocator +
    channels.issuer + channels.adaptation

def generalEquilibriumEffect (channels : EffectChannels) : Scalar :=
  channels.direct + feedbackEffect channels

theorem generalEquilibrium_eq_direct_of_zero_feedback
    (channels : EffectChannels)
    (zeroFeedback : feedbackEffect channels = 0) :
    generalEquilibriumEffect channels = channels.direct := by
  simp [generalEquilibriumEffect, zeroFeedback]

end LeanFinance.StrategyEcology
