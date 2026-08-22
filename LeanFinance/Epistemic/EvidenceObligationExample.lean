import LeanFinance.Epistemic.EvidenceObligation

namespace LeanFinance.Epistemic.EvidenceObligationExample

inductive History where
  | honest
  | hiddenSweep
  | seedCherryPick
  | futureLeak
  | costModelTampering
  | combinedSweepAndLeak
  deriving Repr, DecidableEq

inductive Channel where
  | resultBundle
  | rfc3161Timestamp
  | executionReceipt
  | dataAccessReceipt
  | configurationReceipt
  deriving Repr, DecidableEq

/-- `true` means this channel exposes a violation. Publication artifacts and
timestamps remain identical across all histories in this example. -/
def observe : Channel → History → Bool
  | .resultBundle, _ => false
  | .rfc3161Timestamp, _ => false
  | .executionReceipt, .hiddenSweep => true
  | .executionReceipt, .seedCherryPick => true
  | .executionReceipt, .combinedSweepAndLeak => true
  | .executionReceipt, _ => false
  | .dataAccessReceipt, .futureLeak => true
  | .dataAccessReceipt, .combinedSweepAndLeak => true
  | .dataAccessReceipt, _ => false
  | .configurationReceipt, .costModelTampering => true
  | .configurationReceipt, _ => false

def honest : History → Prop
  | .honest => True
  | _ => False

def knownExecutionAttacks : History → Prop
  | .hiddenSweep | .seedCherryPick => True
  | _ => False

def knownBeforeConfigurationAttack : History → Prop
  | .hiddenSweep | .seedCherryPick | .futureLeak
  | .combinedSweepAndLeak => True
  | _ => False

/-- Hidden parameter search and random-seed cherry-picking are distinct
techniques but induce the same evidence obligation in this workflow. -/
theorem hidden_sweep_and_seed_cherry_pick_same_epistemic_class :
    SameSeparatorSignature
      observe honest .hiddenSweep .seedCherryPick := by
  intro honestHistory honestReference evidenceChannel
  cases honestHistory <;> simp [honest] at honestReference
  cases evidenceChannel <;> simp [Separates, observe]

/-- A combined sweep and future-data leak contains every separator obligation
of the hidden-sweep attack. -/
theorem hidden_sweep_signature_subsumed_by_combined_attack :
    SeparatorSignatureSubsumedBy
      observe honest .hiddenSweep .combinedSweepAndLeak := by
  intro honestHistory honestReference evidenceChannel separates
  cases honestHistory <;> simp [honest] at honestReference
  cases evidenceChannel <;> simp [Separates, observe] at separates ⊢

/-- The subsumption is strict because the combined attack additionally
requires a data-access separator. -/
theorem combined_attack_not_subsumed_by_hidden_sweep :
    ¬ SeparatorSignatureSubsumedBy
      observe honest .combinedSweepAndLeak .hiddenSweep := by
  intro subsumed
  have dataSeparator :
      Separates observe .dataAccessReceipt
        .honest .combinedSweepAndLeak := by
    simp [Separates, observe]
  have impossible :=
    subsumed .honest True.intro .dataAccessReceipt dataSeparator
  simp [Separates, observe] at impossible

/-- Future-data access introduces an obligation absent from the two known
execution-selection attacks. -/
theorem future_leak_introduces_data_access_obligation :
    IntroducesSeparatorObligation
      observe honest knownExecutionAttacks
      .futureLeak .dataAccessReceipt := by
  refine ⟨.honest, True.intro, ?_, ?_⟩
  · simp [Separates, observe]
  · intro prior known
    cases prior <;>
      simp [knownExecutionAttacks, Separates, observe] at known ⊢

/-- Consequently the future-data leak is a new epistemic attack class relative
to hidden sweeps and seed cherry-picking. -/
theorem future_leak_is_epistemically_novel :
    EpistemicallyNovel
      observe honest knownExecutionAttacks .futureLeak :=
  introduced_separator_implies_epistemic_novelty
    observe honest knownExecutionAttacks
    .futureLeak .dataAccessReceipt
    future_leak_introduces_data_access_obligation

/-- Cost-model tampering introduces a third causal-boundary obligation that is
absent from execution and data-access attacks. -/
theorem cost_model_tampering_introduces_configuration_obligation :
    IntroducesSeparatorObligation
      observe honest knownBeforeConfigurationAttack
      .costModelTampering .configurationReceipt := by
  refine ⟨.honest, True.intro, ?_, ?_⟩
  · simp [Separates, observe]
  · intro prior known
    cases prior <;>
      simp [knownBeforeConfigurationAttack, Separates, observe] at known ⊢

theorem cost_model_tampering_is_epistemically_novel :
    EpistemicallyNovel
      observe honest knownBeforeConfigurationAttack
      .costModelTampering :=
  introduced_separator_implies_epistemic_novelty
    observe honest knownBeforeConfigurationAttack
    .costModelTampering .configurationReceipt
    cost_model_tampering_introduces_configuration_obligation

/-- The observed refinement from the repository raises exact evidence debt from
six to eight, so its marginal obligation is two. -/
theorem observed_cost_model_tampering_marginal_debt :
    MarginalEvidenceDebt 6 8 = 2 := by
  decide

end LeanFinance.Epistemic.EvidenceObligationExample
