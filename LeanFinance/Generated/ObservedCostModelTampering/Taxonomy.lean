import LeanFinance.Epistemic.EvidenceTaxonomy
import LeanFinance.Generated.ObservedCostModelTampering.Evidence

namespace LeanFinance.Generated.ObservedCostModelTampering.Taxonomy

open LeanFinance.Epistemic
open LeanFinance.Generated.ObservedCostModelTampering.Evidence

/-- The original pre-tampering attack catalog used for novelty comparison. -/
def knownAttacks : List History :=
  [.undeclaredBaseline, .hiddenSweep, .futureLeak, .dualAttack]

/-- The exact minimum basis before the control-plane mutation was observed. -/
def legacyBasis : List Channel :=
  [.selfReport,
    .targetedReceipt_executeHiddenSweep,
    .targetedReceipt_readFutureData]

/-- The refined minimum basis after the control-plane mutation was admitted. -/
def refinedBasis : List Channel :=
  [.selfReport,
    .targetedReceipt_executeHiddenSweep,
    .targetedReceipt_readFutureData,
    .targetedReceipt_tamperCostModel]

theorem undeclared_baseline_signature
    (evidenceChannel : Channel) :
    SeparatorSignatureAt observe .honest .undeclaredBaseline
        evidenceChannel ↔
      evidenceChannel = .selfReport := by
  cases evidenceChannel <;>
    simp [SeparatorSignatureAt, Separates, observe]

theorem hidden_sweep_signature
    (evidenceChannel : Channel) :
    SeparatorSignatureAt observe .honest .hiddenSweep
        evidenceChannel ↔
      evidenceChannel = .fullExecutorLog ∨
        evidenceChannel = .targetedReceipt_executeHiddenSweep := by
  cases evidenceChannel <;>
    simp [SeparatorSignatureAt, Separates, observe]

theorem future_leak_signature
    (evidenceChannel : Channel) :
    SeparatorSignatureAt observe .honest .futureLeak
        evidenceChannel ↔
      evidenceChannel = .fullExecutorLog ∨
        evidenceChannel = .targetedReceipt_readFutureData := by
  cases evidenceChannel <;>
    simp [SeparatorSignatureAt, Separates, observe]

theorem cost_model_tampering_signature
    (evidenceChannel : Channel) :
    SeparatorSignatureAt observe .honest .costModelTampering
        evidenceChannel ↔
      evidenceChannel = .targetedReceipt_tamperCostModel := by
  cases evidenceChannel <;>
    simp [SeparatorSignatureAt, Separates, observe]

theorem dual_attack_signature
    (evidenceChannel : Channel) :
    SeparatorSignatureAt observe .honest .dualAttack
        evidenceChannel ↔
      evidenceChannel = .fullExecutorLog ∨
        evidenceChannel = .targetedReceipt_executeHiddenSweep ∨
        evidenceChannel = .targetedReceipt_readFutureData := by
  cases evidenceChannel <;>
    simp [SeparatorSignatureAt, Separates, observe]

/-- Different action orders can collapse into one evidence-obligation class. -/
theorem dual_attack_order_variants_share_signature :
    SameSeparatorSignatureAt observe .honest .dualAttack .history16 := by
  intro evidenceChannel
  cases evidenceChannel <;>
    simp [SeparatorSignatureAt, Separates, observe]

theorem dual_attack_order_variants_are_distinct_histories :
    (History.dualAttack : History) ≠ .history16 := by
  decide

theorem syntactically_distinct_attacks_can_be_epistemically_equivalent :
    (History.dualAttack : History) ≠ .history16 ∧
      SameSeparatorSignatureAt observe .honest .dualAttack .history16 :=
  ⟨dual_attack_order_variants_are_distinct_histories,
    dual_attack_order_variants_share_signature⟩

/-- Any basis detecting a hidden sweep also detects the hidden+future composite,
    but the converse fails because a future-data receipt alone detects the
    composite without detecting a pure hidden sweep. -/
theorem hidden_signature_included_in_dual :
    SeparatorSignatureIncludedAt
      observe .honest .hiddenSweep .dualAttack := by
  intro evidenceChannel separates
  cases evidenceChannel <;>
    simp [SeparatorSignatureAt, Separates, observe] at separates ⊢

theorem dual_signature_not_included_in_hidden :
    ¬ SeparatorSignatureIncludedAt
      observe .honest .dualAttack .hiddenSweep := by
  intro included
  have futureSeparatesDual :
      SeparatorSignatureAt observe .honest .dualAttack
        .targetedReceipt_readFutureData := by
    simp [SeparatorSignatureAt, Separates, observe]
  have futureSeparatesHidden :=
    included .targetedReceipt_readFutureData futureSeparatesDual
  simpa [SeparatorSignatureAt, Separates, observe] using
    futureSeparatesHidden

/-- The cost-model mutation has no exact class among the known declaration,
    hidden-execution, future-data, or dual-attack obligations. -/
theorem cost_model_tampering_is_signature_novel :
    EpistemicallyNovelAt
      observe .honest knownAttacks .costModelTampering := by
  intro previous member same
  have previousCases :
      previous = .undeclaredBaseline ∨
        previous = .hiddenSweep ∨
        previous = .futureLeak ∨
        previous = .dualAttack := by
    simpa [knownAttacks] using member
  rcases previousCases with rfl | rfl | rfl | rfl <;>
    have atTamper := same .targetedReceipt_tamperCostModel <;>
    simp [SeparatorSignatureAt, Separates, observe] at atTamper

/-- Its sole separator channel was irrelevant to every known attack. -/
theorem cost_model_tampering_introduces_unseen_separator :
    IntroducesUnseenSeparatorAt
      observe .honest knownAttacks .costModelTampering := by
  refine ⟨.targetedReceipt_tamperCostModel, ?_, ?_⟩
  · simp [SeparatorSignatureAt, Separates, observe]
  · intro previous member previousSeparates
    have previousCases :
        previous = .undeclaredBaseline ∨
          previous = .hiddenSweep ∨
          previous = .futureLeak ∨
          previous = .dualAttack := by
      simpa [knownAttacks] using member
    rcases previousCases with rfl | rfl | rfl | rfl <;>
      simp [SeparatorSignatureAt, Separates, observe] at previousSeparates

/-- The old exact evidence basis cannot see the control-plane mutation. -/
theorem cost_model_tampering_is_basis_novel :
    BasisNovelAt
      observe legacyBasis .honest .costModelTampering := by
  intro detected
  rcases detected with
    ⟨evidenceChannel, member, separates⟩
  have evidenceCases :
      evidenceChannel = .selfReport ∨
        evidenceChannel = .targetedReceipt_executeHiddenSweep ∨
        evidenceChannel = .targetedReceipt_readFutureData := by
    simpa [legacyBasis] using member
  rcases evidenceCases with rfl | rfl | rfl <;>
    simp [SeparatorSignatureAt, Separates, observe] at separates

/-- Adding the targeted control-plane receipt closes that new obligation. -/
theorem refined_basis_detects_cost_model_tampering :
    SelectionSeparatesAt
      observe refinedBasis .honest .costModelTampering := by
  refine ⟨.targetedReceipt_tamperCostModel, ?_, ?_⟩
  · simp [refinedBasis]
  · simp [SeparatorSignatureAt, Separates, observe]

/-- The observed trace satisfies the full strong-novelty criterion. -/
theorem cost_model_tampering_is_new_observation_boundary :
    NewObservationBoundaryAt
      observe legacyBasis .honest knownAttacks .costModelTampering :=
  ⟨cost_model_tampering_is_signature_novel,
    cost_model_tampering_is_basis_novel,
    cost_model_tampering_introduces_unseen_separator⟩

/-- The second ordering of the dual attack is not novel because its separator
    signature already occurs in the catalog. -/
theorem reordered_dual_attack_is_not_signature_novel :
    ¬ EpistemicallyNovelAt
      observe .honest knownAttacks .history16 := by
  intro novel
  exact novel .dualAttack (by simp [knownAttacks])
    dual_attack_order_variants_share_signature

end LeanFinance.Generated.ObservedCostModelTampering.Taxonomy
