import LeanFinance.Epistemic.RobustFiniteSynthesis

namespace LeanFinance.Epistemic.RobustFiniteSynthesisExample

inductive History where
  | honest
  | attack
  deriving Repr, DecidableEq

inductive Channel where
  | providerAReceipt1
  | providerAReceipt2
  | providerBReceipt
  deriving Repr, DecidableEq

inductive Observation where
  | clean
  | violation
  deriving Repr, DecidableEq

def histories : List History :=
  [.honest, .attack]

def channels : List Channel :=
  [.providerAReceipt1, .providerAReceipt2, .providerBReceipt]

def observe (_channel : Channel) : History → Observation
  | .honest => .clean
  | .attack => .violation

def claim : History → Bool
  | .honest => true
  | .attack => false

def cost : Channel → Nat
  | .providerAReceipt1 => 1
  | .providerAReceipt2 => 1
  | .providerBReceipt => 2

def model : BoundedEvidenceModel History Channel Observation :=
  {
    histories := histories
    channels := channels
    observe := observe
    claim := claim
    cost := cost
  }

inductive Fault where
  | none
  | compromiseProviderA
  | compromiseProviderB
  deriving Repr, DecidableEq

def compromised : Fault → Channel → Bool
  | .none, _ => false
  | .compromiseProviderA, .providerAReceipt1 => true
  | .compromiseProviderA, .providerAReceipt2 => true
  | .compromiseProviderA, .providerBReceipt => false
  | .compromiseProviderB, .providerBReceipt => true
  | .compromiseProviderB, _ => false

def faultRank : Fault → Nat
  | .none => 0
  | _ => 1

def faultModel : BoundedFaultModel Channel Fault :=
  {
    faults := [.none, .compromiseProviderA, .compromiseProviderB]
    compromised := compromised
    faultRank := faultRank
  }

abbrev Candidate := Fin 8

def bitSelected (mask index : Nat) : Bool :=
  ((mask / (2 ^ index)) % 2) == 1

def decodeMask (mask : Nat) : List Channel :=
  (if bitSelected mask 0 then [.providerAReceipt1] else []) ++
  (if bitSelected mask 1 then [.providerAReceipt2] else []) ++
  (if bitSelected mask 2 then [.providerBReceipt] else [])

def decode (candidate : Candidate) : List Channel :=
  decodeMask candidate.val

/-- One receipt from provider A and one from provider B. -/
def selected : Candidate :=
  ⟨5, by decide⟩

/-- Two receipt items controlled by the same provider. -/
def sameDomainDuplicates : Candidate :=
  ⟨3, by decide⟩

theorem selected_checker_accepts :
    robustBoundedVerifiesBool
      model faultModel (decode selected) 2 = true := by
  decide

theorem selected_robustly_verifies :
    RobustBoundedSelectionVerifies
      model faultModel (decode selected) 2 :=
  robustBoundedVerifiesBool_sound
    model faultModel (decode selected) 2
    selected_checker_accepts

/-- The two provider-A receipts verify in the no-fault case. -/
theorem same_domain_duplicates_connectivity_one :
    RobustBoundedSelectionVerifies
      model faultModel (decode sameDomainDuplicates) 1 :=
  robustBoundedVerifiesBool_sound
    model faultModel (decode sameDomainDuplicates) 1
    (by decide)

/-- Item multiplicity inside one trust domain does not survive compromise of
that domain. -/
theorem same_domain_duplicates_not_connectivity_two :
    ¬ RobustBoundedSelectionVerifies
      model faultModel (decode sameDomainDuplicates) 2 := by
  intro verified
  have accepted :=
    robustBoundedVerifiesBool_complete
      model faultModel (decode sameDomainDuplicates) 2 verified
  have rejected :
      robustBoundedVerifiesBool
        model faultModel (decode sameDomainDuplicates) 2 ≠ true := by
    decide
  exact rejected accepted

theorem selected_cost_three :
    selectionCost model (decode selected) = 3 := by
  decide

theorem duplicate_cost_two :
    selectionCost model (decode sameDomainDuplicates) = 2 := by
  decide

/-- Kernel computation checks all eight evidence subsets. -/
theorem checkerAcceptedCostMinimal :
    ∀ candidate : Candidate,
      robustBoundedVerifiesBool
          model faultModel (decode candidate) 2 = true →
        selectionCost model (decode selected) ≤
          selectionCost model (decode candidate) := by
  decide

/-- The cross-provider selection is exact minimum cost among all designs that
tolerate either provider compromise. -/
theorem selected_is_minimum_cost_robust_portfolio
    (candidate : Candidate)
    (candidateVerifies :
      RobustBoundedSelectionVerifies
        model faultModel (decode candidate) 2) :
    selectionCost model (decode selected) ≤
      selectionCost model (decode candidate) :=
  checkerAcceptedCostMinimal candidate
    (robustBoundedVerifiesBool_complete
      model faultModel (decode candidate) 2 candidateVerifies)

/-- A cheaper same-provider duplicate design is sufficient without faults but
fails the target resilience level. -/
theorem cheaper_duplicate_is_not_robust :
    selectionCost model (decode sameDomainDuplicates) <
        selectionCost model (decode selected) ∧
      ¬ RobustBoundedSelectionVerifies
        model faultModel (decode sameDomainDuplicates) 2 := by
  exact ⟨by decide,
    same_domain_duplicates_not_connectivity_two⟩

end LeanFinance.Epistemic.RobustFiniteSynthesisExample
