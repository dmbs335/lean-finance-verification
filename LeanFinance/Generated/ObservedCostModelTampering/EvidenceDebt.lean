import LeanFinance.Epistemic.EvidenceDebt
import LeanFinance.Generated.WorkflowCEGIS
import LeanFinance.Generated.ObservedCostModelTampering.CEGIS

namespace LeanFinance.Generated.ObservedCostModelTampering.EvidenceDebt

open LeanFinance.Epistemic

namespace BaseEvidence :=
  LeanFinance.Generated.WorkflowIntegrity.Evidence
namespace BaseCEGIS :=
  LeanFinance.Generated.WorkflowIntegrity.CEGIS
namespace RefinedEvidence :=
  LeanFinance.Generated.ObservedCostModelTampering.Evidence
namespace RefinedCEGIS :=
  LeanFinance.Generated.ObservedCostModelTampering.CEGIS

/-- Before the cost-model mutation entered the adversarial model, the minimum
    repair retained the deployed declaration/result/timestamp channels and
    added two targeted receipts. -/
theorem base_total_repair_debt :
    selectionCost BaseEvidence.model BaseCEGIS.refinedSelection = 10 := by
  decide

/-- After the new control-plane mutation is admitted, the minimum repair adds
    the targeted cost-model receipt and has total cost twelve. -/
theorem refined_total_repair_debt :
    selectionCost RefinedEvidence.model RefinedCEGIS.refinedSelection = 12 := by
  decide

/-- The observed attack creates a strict two-unit evidence-debt increase in the
    mandatory-baseline repair problem. -/
theorem cost_model_tampering_adds_two_units_of_repair_debt :
    selectionCost RefinedEvidence.model RefinedCEGIS.refinedSelection =
      selectionCost BaseEvidence.model BaseCEGIS.refinedSelection + 2 := by
  decide

/-- Greenfield optimization exhibits the same marginal debt: the old optimum
    costs six and the conservatively expanded optimum costs eight. -/
theorem cost_model_tampering_adds_two_units_of_greenfield_debt :
    selectionCost RefinedEvidence.model
        (RefinedEvidence.decode RefinedEvidence.selected) =
      selectionCost BaseEvidence.model
        (BaseEvidence.decode BaseEvidence.selected) + 2 := by
  decide

/-- The new attack pressure is exactly the cost of its unique targeted receipt. -/
theorem concrete_attack_pressure :
    attackPressure 10 12 = 2 := by
  decide

end LeanFinance.Generated.ObservedCostModelTampering.EvidenceDebt
