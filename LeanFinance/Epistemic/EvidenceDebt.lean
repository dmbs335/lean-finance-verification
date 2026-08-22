import LeanFinance.Epistemic.FiniteSynthesisCompleteness

namespace LeanFinance.Epistemic

universe u v w x y

/-- Minimum verification cost, with `impossible` representing a candidate
    evidence language in which no selection verifies the bounded claim. -/
inductive EvidenceDebt where
  | finite (cost : Nat)
  | impossible
  deriving Repr, DecidableEq

/-- Order evidence debt by burden. Every finite cost is below impossibility. -/
def DebtLE : EvidenceDebt → EvidenceDebt → Prop
  | .finite left, .finite right => left ≤ right
  | .finite _, .impossible => True
  | .impossible, .finite _ => False
  | .impossible, .impossible => True

theorem debtLE_refl (debt : EvidenceDebt) : DebtLE debt debt := by
  cases debt with
  | finite cost => exact Nat.le_refl cost
  | impossible => exact True.intro

theorem debtLE_trans
    {first second third : EvidenceDebt}
    (firstSecond : DebtLE first second)
    (secondThird : DebtLE second third) :
    DebtLE first third := by
  cases first <;> cases second <;> cases third <;>
    simp [DebtLE] at firstSecond secondThird ⊢
  exact Nat.le_trans firstSecond secondThird

/-- A finite debt certificate supplies a verifying selection and proves that no
    candidate in the declared language has lower cost. -/
structure FiniteEvidenceDebtCertificate
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (Candidate : Type x)
    (decode : Candidate → List Channel) where
  selected : Candidate
  selectedVerifies :
    BoundedSelectionVerifies model (decode selected)
  minimal :
    ∀ candidate,
      BoundedSelectionVerifies model (decode candidate) →
        selectionCost model (decode selected) ≤
          selectionCost model (decode candidate)

/-- An impossibility certificate proves that the complete declared candidate
    language contains no verifying evidence selection. -/
structure ImpossibleEvidenceDebtCertificate
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (Candidate : Type x)
    (decode : Candidate → List Channel) where
  noCandidateVerifies :
    ∀ candidate,
      ¬ BoundedSelectionVerifies model (decode candidate)

/-- Proof-carrying evidence debt is either an exact finite optimum or a proof
    that the current evidence language cannot verify the claim at any cost. -/
inductive EvidenceDebtCertificate
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (Candidate : Type x)
    (decode : Candidate → List Channel) where
  | finite
      (certificate :
        FiniteEvidenceDebtCertificate model Candidate decode)
  | impossible
      (certificate :
        ImpossibleEvidenceDebtCertificate model Candidate decode)

namespace EvidenceDebtCertificate

def debt
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {model : BoundedEvidenceModel History Channel Observation}
    {Candidate : Type x}
    {decode : Candidate → List Channel} :
    EvidenceDebtCertificate model Candidate decode → EvidenceDebt
  | .finite certificate =>
      .finite (selectionCost model (decode certificate.selected))
  | .impossible _ => .impossible

end EvidenceDebtCertificate

/-- One bounded model extends another by adding histories while preserving the
    evidence semantics, claim, costs, and channel catalog on the shared type. -/
structure HistoryModelExtension
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (smaller larger :
      BoundedEvidenceModel History Channel Observation) where
  historiesIncluded :
    ∀ history,
      history ∈ smaller.histories →
        history ∈ larger.histories
  channelCatalogPreserved : smaller.channels = larger.channels
  observePreserved :
    ∀ channel history,
      smaller.observe channel history = larger.observe channel history
  claimPreserved :
    ∀ history,
      smaller.claim history = larger.claim history
  costPreserved :
    ∀ channel,
      smaller.cost channel = larger.cost channel

namespace HistoryModelExtension

theorem selectionCostPreserved
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {smaller larger :
      BoundedEvidenceModel History Channel Observation}
    (extension : HistoryModelExtension smaller larger)
    (selected : List Channel) :
    selectionCost smaller selected = selectionCost larger selected := by
  induction selected with
  | nil => rfl
  | cons head tail ih =>
      simp [selectionCost, extension.costPreserved, ih]

/-- Any selection that verifies an expanded history model also verifies every
    history-restricted predecessor with the same evidence semantics. -/
theorem verifiesSmaller
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {smaller larger :
      BoundedEvidenceModel History Channel Observation}
    (extension : HistoryModelExtension smaller larger)
    {selected : List Channel}
    (verifies : BoundedSelectionVerifies larger selected) :
    BoundedSelectionVerifies smaller selected := by
  intro left leftMember right rightMember claimDifferent
  have largerClaimDifferent :
      larger.claim left ≠ larger.claim right := by
    intro sameClaim
    apply claimDifferent
    calc
      smaller.claim left = larger.claim left :=
        extension.claimPreserved left
      _ = larger.claim right := sameClaim
      _ = smaller.claim right :=
        (extension.claimPreserved right).symm
  rcases verifies
      left (extension.historiesIncluded left leftMember)
      right (extension.historiesIncluded right rightMember)
      largerClaimDifferent with
    ⟨channel, channelSelected, separates⟩
  refine ⟨channel, channelSelected, ?_⟩
  intro sameObservation
  apply separates
  calc
    larger.observe channel left = smaller.observe channel left :=
      (extension.observePreserved channel left).symm
    _ = smaller.observe channel right := sameObservation
    _ = larger.observe channel right :=
      extension.observePreserved channel right

end HistoryModelExtension

/-- Expanding the adversarial history model cannot reduce evidence debt when
    the evidence language and its costs are fixed. -/
theorem evidence_debt_monotone_under_history_expansion
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {Candidate : Type x}
    {smaller larger :
      BoundedEvidenceModel History Channel Observation}
    {decode : Candidate → List Channel}
    (extension : HistoryModelExtension smaller larger)
    (smallerCertificate :
      EvidenceDebtCertificate smaller Candidate decode)
    (largerCertificate :
      EvidenceDebtCertificate larger Candidate decode) :
    DebtLE smallerCertificate.debt largerCertificate.debt := by
  cases smallerCertificate with
  | finite smallerFinite =>
      cases largerCertificate with
      | finite largerFinite =>
          change
            selectionCost smaller (decode smallerFinite.selected) ≤
              selectionCost larger (decode largerFinite.selected)
          calc
            selectionCost smaller (decode smallerFinite.selected) ≤
                selectionCost smaller (decode largerFinite.selected) :=
              smallerFinite.minimal
                largerFinite.selected
                (extension.verifiesSmaller
                  largerFinite.selectedVerifies)
            _ = selectionCost larger (decode largerFinite.selected) :=
              extension.selectionCostPreserved
                (decode largerFinite.selected)
      | impossible _ => exact True.intro
  | impossible smallerImpossible =>
      cases largerCertificate with
      | finite largerFinite =>
          exact False.elim
            (smallerImpossible.noCandidateVerifies
              largerFinite.selected
              (extension.verifiesSmaller
                largerFinite.selectedVerifies))
      | impossible _ => exact True.intro

/-- An embedding of a smaller candidate language into a larger one. The same
    evidence selection must decode identically after embedding. -/
structure CandidateLanguageExtension
    {Channel : Type v}
    (SmallerCandidate : Type x)
    (LargerCandidate : Type y)
    (smallerDecode : SmallerCandidate → List Channel)
    (largerDecode : LargerCandidate → List Channel) where
  embed : SmallerCandidate → LargerCandidate
  decodePreserved :
    ∀ candidate,
      largerDecode (embed candidate) = smallerDecode candidate

/-- Enlarging the candidate evidence language cannot increase minimum debt.
    It may also turn an impossible language into a finite one. -/
theorem evidence_debt_antitone_under_candidate_expansion
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {SmallerCandidate : Type x}
    {LargerCandidate : Type y}
    {model : BoundedEvidenceModel History Channel Observation}
    {smallerDecode : SmallerCandidate → List Channel}
    {largerDecode : LargerCandidate → List Channel}
    (extension :
      CandidateLanguageExtension
        SmallerCandidate LargerCandidate
        smallerDecode largerDecode)
    (smallerCertificate :
      EvidenceDebtCertificate
        model SmallerCandidate smallerDecode)
    (largerCertificate :
      EvidenceDebtCertificate
        model LargerCandidate largerDecode) :
    DebtLE largerCertificate.debt smallerCertificate.debt := by
  cases smallerCertificate with
  | finite smallerFinite =>
      have embeddedVerifies :
          BoundedSelectionVerifies model
            (largerDecode (extension.embed smallerFinite.selected)) := by
        rw [extension.decodePreserved]
        exact smallerFinite.selectedVerifies
      cases largerCertificate with
      | finite largerFinite =>
          change
            selectionCost model (largerDecode largerFinite.selected) ≤
              selectionCost model (smallerDecode smallerFinite.selected)
          calc
            selectionCost model (largerDecode largerFinite.selected) ≤
                selectionCost model
                  (largerDecode
                    (extension.embed smallerFinite.selected)) :=
              largerFinite.minimal
                (extension.embed smallerFinite.selected)
                embeddedVerifies
            _ = selectionCost model
                  (smallerDecode smallerFinite.selected) :=
              congrArg (selectionCost model)
                (extension.decodePreserved smallerFinite.selected)
      | impossible largerImpossible =>
          exact False.elim
            (largerImpossible.noCandidateVerifies
              (extension.embed smallerFinite.selected)
              embeddedVerifies)
  | impossible _ =>
      cases largerCertificate with
      | finite _ => exact True.intro
      | impossible _ => exact True.intro

/-- Increase in finite debt caused by an expanded attack model. -/
def attackPressure (baseline attacked : Nat) : Nat :=
  attacked - baseline

/-- Debt removed by adding a richer evidence language to a fixed attack model. -/
def sensorRelief (attacked repaired : Nat) : Nat :=
  attacked - repaired

/-- For finite debts, attack pressure and sensor relief obey a balance law.
    The attacked debt is the common intermediate burden. -/
theorem finite_evidence_debt_balance
    {baseline attacked repaired : Nat}
    (baselineLe : baseline ≤ attacked)
    (repairedLe : repaired ≤ attacked) :
    baseline + attackPressure baseline attacked =
      repaired + sensorRelief attacked repaired := by
  calc
    baseline + attackPressure baseline attacked =
        (attacked - baseline) + baseline := by
      simp [attackPressure, Nat.add_comm]
    _ = attacked := Nat.sub_add_cancel baselineLe
    _ = (attacked - repaired) + repaired :=
      (Nat.sub_add_cancel repairedLe).symm
    _ = repaired + sensorRelief attacked repaired := by
      simp [sensorRelief, Nat.add_comm]

end LeanFinance.Epistemic
