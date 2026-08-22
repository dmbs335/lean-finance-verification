import LeanFinance.Generated.WorkflowEvidence

namespace LeanFinance.Generated.WorkflowIntegrity.Evidence

/-- Closed bit computations used by the generated repair witness. Keeping these
    facts in the forwarding module lets the generated proof remain stable across
    Lean simplifier changes while preserving byte-for-byte generator output. -/
@[simp] theorem selectedRepair_bit0 :
    ¬ ((((6 : Fin 8) : Nat) % 2) = 1) := by
  decide

@[simp] theorem selectedRepair_bit1 :
    ((((6 : Fin 8) : Nat) / 2) % 2) = 1 := by
  decide

@[simp] theorem selectedRepair_bit2 :
    ((((6 : Fin 8) : Nat) / (2 ^ 2)) % 2) = 1 := by
  decide

end LeanFinance.Generated.WorkflowIntegrity.Evidence
