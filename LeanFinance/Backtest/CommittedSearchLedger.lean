import LeanFinance.Backtest.Artifact
import LeanFinance.Backtest.Decision

namespace LeanFinance.Backtest

/-- One preregistered hypothesis trial. `previousCommitment` links the entry to
    the prior committed entry. The cryptographic preimage check is performed by
    the empirical adapter; Lean verifies the declared chain structure and time
    ordering. -/
structure RegisteredTrial where
  hypothesisId : String
  parameters : ArtifactRef .parameterSet
  code : ArtifactRef .sourceCode
  registeredAt : Timestamp
  previousCommitment : Option (ArtifactRef .searchLedger)
  commitment : ArtifactRef .searchLedger
  deriving Repr

namespace RegisteredTrial

def Bound (trial : RegisteredTrial) : Prop :=
  NonEmptyString trial.hypothesisId ∧
    trial.parameters.Valid ∧
    trial.code.Valid ∧
    trial.commitment.Valid

end RegisteredTrial

/-- Entries are stored oldest first. -/
structure CommittedSearchLedger where
  entries : List RegisteredTrial
  deriving Repr

/-- The second entry explicitly commits to the first entry's commitment. -/
def LedgerLinks (previous current : RegisteredTrial) : Prop :=
  current.previousCommitment = some previous.commitment

/-- Structural validity of the committed ledger. This checks entry binding,
    commitment linkage, and monotone registration time. -/
def ValidCommittedChain : List RegisteredTrial → Prop
  | [] => True
  | [entry] => entry.Bound
  | first :: second :: rest =>
      first.Bound ∧
      second.Bound ∧
      LedgerLinks first second ∧
      first.registeredAt ≤ second.registeredAt ∧
      ValidCommittedChain (second :: rest)

def CommittedSearchLedger.Valid (ledger : CommittedSearchLedger) : Prop :=
  ValidCommittedChain ledger.entries

/-- `after` is append-only with respect to `before` exactly when the complete old
    history is retained as a prefix. -/
def IsAppendOnlyExtension
    (before after : CommittedSearchLedger) : Prop :=
  ∃ suffix, after.entries = before.entries ++ suffix

theorem appendOnly_refl (ledger : CommittedSearchLedger) :
    IsAppendOnlyExtension ledger ledger := by
  refine ⟨[], ?_⟩
  simp

theorem appendOnly_trans
    {first second third : CommittedSearchLedger}
    (firstSecond : IsAppendOnlyExtension first second)
    (secondThird : IsAppendOnlyExtension second third) :
    IsAppendOnlyExtension first third := by
  rcases firstSecond with ⟨middleSuffix, middleEq⟩
  rcases secondThird with ⟨finalSuffix, finalEq⟩
  refine ⟨middleSuffix ++ finalSuffix, ?_⟩
  calc
    third.entries = second.entries ++ finalSuffix := finalEq
    _ = (first.entries ++ middleSuffix) ++ finalSuffix := by rw [middleEq]
    _ = first.entries ++ (middleSuffix ++ finalSuffix) :=
      List.append_assoc _ _ _

/-- Last chain commitment, used to bind the complete ledger to an external
    timestamped anchor. -/
def lastCommitment : List RegisteredTrial → Option (ArtifactRef .searchLedger)
  | [] => none
  | [entry] => some entry.commitment
  | _ :: rest => lastCommitment rest

/-- Externally published commitment to a complete ledger prefix. `anchoredAt`
    records when the commitment became externally observable. -/
structure LedgerAnchor where
  commitment : ArtifactRef .searchLedger
  entryCount : Nat
  anchoredAt : Timestamp
  deriving Repr

/-- The anchor commits to both the ledger length and its terminal chain digest. -/
def AnchorsLedger
    (anchor : LedgerAnchor)
    (ledger : CommittedSearchLedger) : Prop :=
  anchor.commitment.Valid ∧
    anchor.entryCount = ledger.entries.length ∧
    lastCommitment ledger.entries = some anchor.commitment

def AnchorAvailableAt
    (anchor : LedgerAnchor)
    (decision : Decision) : Prop :=
  anchor.anchoredAt ≤ decision.decisionTime

/-- The selected strategy/parameter pair must have appeared in the ledger no
    later than the decision time. -/
def ChoicePreRegistered
    (ledger : CommittedSearchLedger)
    (decision : Decision) : Prop :=
  ∃ trial,
    trial ∈ ledger.entries ∧
    trial.hypothesisId = decision.strategyId ∧
    trial.parameters.digest = decision.parameterHash ∧
    trial.registeredAt ≤ decision.decisionTime

structure PreRegistrationCertificate
    (ledger : CommittedSearchLedger)
    (decision : Decision) : Prop where
  validLedger : ledger.Valid
  choicePreRegistered : ChoicePreRegistered ledger decision

/-- Stronger certificate requiring the full ledger prefix to have been anchored
    no later than the decision. This closes the "construct the whole ledger
    after seeing the result" loophole inside the formal contract, assuming the
    external timestamp/commitment evidence is authentic. -/
structure AnchoredPreRegistrationCertificate
    (ledger : CommittedSearchLedger)
    (decision : Decision) where
  anchor : LedgerAnchor
  validLedger : ledger.Valid
  anchorsLedger : AnchorsLedger anchor ledger
  anchorAvailable : AnchorAvailableAt anchor decision
  choicePreRegistered : ChoicePreRegistered ledger decision

theorem PreRegistrationCertificate.registeredBeforeDecision
    (ledger : CommittedSearchLedger)
    (decision : Decision)
    (certificate : PreRegistrationCertificate ledger decision) :
    ∃ trial,
      trial ∈ ledger.entries ∧
      trial.parameters.digest = decision.parameterHash ∧
      trial.registeredAt ≤ decision.decisionTime := by
  rcases certificate.choicePreRegistered with
    ⟨trial, member, _strategyMatches, parameterMatches, registeredBefore⟩
  exact ⟨trial, member, parameterMatches, registeredBefore⟩

theorem AnchoredPreRegistrationCertificate.anchor_before_decision
    (ledger : CommittedSearchLedger)
    (decision : Decision)
    (certificate : AnchoredPreRegistrationCertificate ledger decision) :
    certificate.anchor.anchoredAt ≤ decision.decisionTime :=
  certificate.anchorAvailable

end LeanFinance.Backtest
