import LeanFinance.Epistemic.EvidenceDebt
import LeanFinance.Generated.ObservedCostModelTampering.Evidence

namespace LeanFinance.Generated.ObservedCostModelTampering.DebtEvolution

open LeanFinance.Epistemic
open LeanFinance.Generated.ObservedCostModelTampering.Evidence

/-- Histories that do not contain the newly learned cost-model mutation. The
    targeted receipt is used here only to identify the conservative old-history
    image inside the refined common history type. -/
def legacyHistories : List History :=
  histories.filter (fun history =>
    observe .targetedReceipt_tamperCostModel history == .obs9)

def legacyModel :
    BoundedEvidenceModel History Channel Observation :=
  { model with histories := legacyHistories }

abbrev attackedModel :
    BoundedEvidenceModel History Channel Observation :=
  model

theorem legacy_history_count : legacyHistories.length = 10 := by
  decide

theorem attacked_history_count : attackedModel.histories.length = 32 := by
  decide

def observedAttackHistoryExtension :
    HistoryModelExtension legacyModel attackedModel :=
  {
    historiesIncluded := by
      intro history member
      have filtered :
          history ∈ histories ∧
            observe .targetedReceipt_tamperCostModel history == .obs9 := by
        simpa [legacyModel, legacyHistories] using member
      exact filtered.1
    channelCatalogPreserved := rfl
    observePreserved := by
      intro channel history
      rfl
    claimPreserved := by
      intro history
      rfl
    costPreserved := by
      intro channel
      rfl
  }

/-- The pre-attack evidence language contains every subset of the six channels
    that existed before the targeted cost-model receipt was introduced. -/
abbrev LegacyCandidate := Fin 64

def legacyDecodeMask (mask : Nat) : List Channel :=
  (if bitSelected mask 0 then [.selfReport] else [])
    ++ (if bitSelected mask 1 then [.resultBundle] else [])
    ++ (if bitSelected mask 2 then [.rfc3161Anchor] else [])
    ++ (if bitSelected mask 3 then [.fullExecutorLog] else [])
    ++ (if bitSelected mask 4 then
          [.targetedReceipt_executeHiddenSweep] else [])
    ++ (if bitSelected mask 5 then
          [.targetedReceipt_readFutureData] else [])

def legacyDecode (candidate : LegacyCandidate) : List Channel :=
  legacyDecodeMask candidate.val

def legacySelected : LegacyCandidate :=
  ⟨49, by decide⟩

theorem legacySelectedVerifies :
    BoundedSelectionVerifies legacyModel
      (legacyDecode legacySelected) := by
  apply boundedVerifiesBool_sound
  decide

theorem legacyCheckerCostMinimal :
    ∀ candidate : LegacyCandidate,
      boundedVerifiesBool legacyModel
          (legacyDecode candidate) = true →
        selectionCost legacyModel
            (legacyDecode legacySelected) ≤
          selectionCost legacyModel
            (legacyDecode candidate) := by
  decide

theorem legacyCostMinimal
    (candidate : LegacyCandidate)
    (candidateVerifies :
      BoundedSelectionVerifies legacyModel
        (legacyDecode candidate)) :
    selectionCost legacyModel
        (legacyDecode legacySelected) ≤
      selectionCost legacyModel
        (legacyDecode candidate) :=
  legacyCheckerCostMinimal candidate
    (boundedVerifiesBool_complete
      legacyModel (legacyDecode candidate)
      candidateVerifies)

def legacyDebtCertificate :
    EvidenceDebtCertificate
      legacyModel LegacyCandidate legacyDecode :=
  .finite
    {
      selected := legacySelected
      selectedVerifies := legacySelectedVerifies
      minimal := legacyCostMinimal
    }

/-- Once the cost-model mutation history is admitted, no combination of the old
    six-channel language can verify the claim. -/
theorem attackedLegacyCheckerRejects :
    ∀ candidate : LegacyCandidate,
      boundedVerifiesBool attackedModel
        (legacyDecode candidate) = false := by
  decide

theorem attackedLegacyNoCandidateVerifies :
    ∀ candidate : LegacyCandidate,
      ¬ BoundedSelectionVerifies attackedModel
          (legacyDecode candidate) := by
  intro candidate candidateVerifies
  have accepted :
      boundedVerifiesBool attackedModel
        (legacyDecode candidate) = true :=
    boundedVerifiesBool_complete
      attackedModel (legacyDecode candidate)
      candidateVerifies
  have rejected := attackedLegacyCheckerRejects candidate
  rw [rejected] at accepted
  contradiction

def attackedLegacyDebtCertificate :
    EvidenceDebtCertificate
      attackedModel LegacyCandidate legacyDecode :=
  .impossible
    {
      noCandidateVerifies := attackedLegacyNoCandidateVerifies
    }

/-- The expanded seven-channel language includes the new targeted control-plane
    receipt and again has a finite optimum. -/
def expandedDebtCertificate :
    EvidenceDebtCertificate
      attackedModel Candidate decode :=
  .finite
    {
      selected := selected
      selectedVerifies := by
        simpa [attackedModel] using selectedBoundedlyVerifies
      minimal := by
        intro candidate candidateVerifies
        simpa [attackedModel] using
          synthesized_selection_is_cost_minimal
            candidate candidateVerifies
    }

def embedLegacyCandidate
    (candidate : LegacyCandidate) : Candidate :=
  ⟨candidate.val, Nat.lt_trans candidate.isLt (by decide)⟩

theorem embeddedLegacyDecodePreserved
    (candidate : LegacyCandidate) :
    decode (embedLegacyCandidate candidate) =
      legacyDecode candidate := by
  change decodeMask candidate.val = legacyDecodeMask candidate.val
  have highBitOff : bitSelected candidate.val 6 = false := by
    simp [bitSelected, Nat.div_eq_of_lt candidate.isLt]
  simp [decodeMask, legacyDecodeMask, highBitOff]

def observedSensorLanguageExtension :
    CandidateLanguageExtension
      LegacyCandidate Candidate
      legacyDecode decode :=
  {
    embed := embedLegacyCandidate
    decodePreserved := embeddedLegacyDecodePreserved
  }

theorem legacy_debt_value :
    legacyDebtCertificate.debt = EvidenceDebt.finite 6 := by
  decide

theorem attacked_old_language_debt_value :
    attackedLegacyDebtCertificate.debt = EvidenceDebt.impossible := rfl

theorem expanded_debt_value :
    expandedDebtCertificate.debt = EvidenceDebt.finite 8 := by
  decide

/-- Adding the observed attack cannot lower debt; in this instance it pushes
    the old evidence language from finite cost to outright impossibility. -/
theorem attack_history_increases_debt :
    DebtLE legacyDebtCertificate.debt
      attackedLegacyDebtCertificate.debt :=
  evidence_debt_monotone_under_history_expansion
    observedAttackHistoryExtension
    legacyDebtCertificate
    attackedLegacyDebtCertificate

/-- Adding the targeted receipt language restores finite verification from the
    impossible old language. -/
theorem sensor_extension_reduces_debt :
    DebtLE expandedDebtCertificate.debt
      attackedLegacyDebtCertificate.debt :=
  evidence_debt_antitone_under_candidate_expansion
    observedSensorLanguageExtension
    attackedLegacyDebtCertificate
    expandedDebtCertificate

/-- After both the attack and its targeted sensor are incorporated, the finite
    optimum rises from 6 to 8: this trace contributes two units of marginal
    evidence debt in the declared cost model. -/
theorem observed_attack_adds_two_units_of_finite_debt :
    ∃ baseline refined,
      legacyDebtCertificate.debt = EvidenceDebt.finite baseline ∧
      expandedDebtCertificate.debt = EvidenceDebt.finite refined ∧
      refined = baseline + 2 := by
  refine ⟨6, 8, legacy_debt_value, expanded_debt_value, ?_⟩
  decide

end LeanFinance.Generated.ObservedCostModelTampering.DebtEvolution
