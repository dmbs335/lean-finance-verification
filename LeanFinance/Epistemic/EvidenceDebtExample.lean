import LeanFinance.Epistemic.EvidenceDebt
import LeanFinance.Generated.WorkflowIntegrity.Evidence
import LeanFinance.Generated.ObservedCostModelTampering.Evidence

namespace LeanFinance.Epistemic.EvidenceDebtExample

namespace Base

abbrev Candidate :=
  LeanFinance.Generated.WorkflowIntegrity.Evidence.Candidate

def debt : Nat :=
  selectionCost
    LeanFinance.Generated.WorkflowIntegrity.Evidence.model
    (LeanFinance.Generated.WorkflowIntegrity.Evidence.decode
      LeanFinance.Generated.WorkflowIntegrity.Evidence.selected)

theorem debt_eq_six : debt = 6 := by
  decide

theorem debt_is_minimal
    (candidate : Candidate)
    (verified :
      BoundedSelectionVerifies
        LeanFinance.Generated.WorkflowIntegrity.Evidence.model
        (LeanFinance.Generated.WorkflowIntegrity.Evidence.decode candidate)) :
    debt ≤
      selectionCost
        LeanFinance.Generated.WorkflowIntegrity.Evidence.model
        (LeanFinance.Generated.WorkflowIntegrity.Evidence.decode candidate) :=
  LeanFinance.Generated.WorkflowIntegrity.Evidence
    .synthesized_selection_is_cost_minimal candidate verified

end Base

namespace Refined

abbrev Candidate :=
  LeanFinance.Generated.ObservedCostModelTampering.Evidence.Candidate

def debt : Nat :=
  selectionCost
    LeanFinance.Generated.ObservedCostModelTampering.Evidence.model
    (LeanFinance.Generated.ObservedCostModelTampering.Evidence.decode
      LeanFinance.Generated.ObservedCostModelTampering.Evidence.selected)

theorem debt_eq_eight : debt = 8 := by
  decide

theorem debt_is_minimal
    (candidate : Candidate)
    (verified :
      BoundedSelectionVerifies
        LeanFinance.Generated.ObservedCostModelTampering.Evidence.model
        (LeanFinance.Generated.ObservedCostModelTampering.Evidence.decode candidate)) :
    debt ≤
      selectionCost
        LeanFinance.Generated.ObservedCostModelTampering.Evidence.model
        (LeanFinance.Generated.ObservedCostModelTampering.Evidence.decode candidate) :=
  LeanFinance.Generated.ObservedCostModelTampering.Evidence
    .synthesized_selection_is_cost_minimal candidate verified

end Refined

/-- Adding the observed cost-model-tampering action and its composed histories
raises the exact greenfield evidence debt by two weighted cost units, even
after the new targeted receipt becomes available. -/
theorem cost_model_tampering_adds_two_units_of_evidence_debt :
    Refined.debt = Base.debt + 2 := by
  rw [Base.debt_eq_six, Refined.debt_eq_eight]

/-- The concrete refinement exhibits positive marginal evidence debt. -/
theorem cost_model_tampering_strictly_increases_evidence_debt :
    Base.debt < Refined.debt := by
  rw [Base.debt_eq_six, Refined.debt_eq_eight]
  decide

end LeanFinance.Epistemic.EvidenceDebtExample
