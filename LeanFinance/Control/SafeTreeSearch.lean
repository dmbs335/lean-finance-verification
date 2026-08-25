namespace LeanFinance.Control

/-- One selected action summary from a finite-horizon robust tree search. -/
structure TreeActionCertificate where
  actionId : Nat
  supportCount : Nat
  minimumSupport : Nat
  safe : Bool
  isBaseline : Bool
  lowerValue : Int
  deriving Repr, DecidableEq

namespace TreeActionCertificate

/-- SPIBB-style admissibility: an action must be safe and either sufficiently
    supported or exactly the registered baseline action. -/
def admissible (certificate : TreeActionCertificate) : Bool :=
  certificate.safe &&
    (decide (certificate.minimumSupport ≤ certificate.supportCount) ||
      certificate.isBaseline)

theorem admitted_action_is_safe
    (certificate : TreeActionCertificate)
    (accepted : certificate.admissible = true) :
    certificate.safe = true := by
  have facts :
      certificate.safe = true ∧
        (certificate.minimumSupport ≤ certificate.supportCount ∨
          certificate.isBaseline = true) := by
    simpa [admissible] using accepted
  exact facts.1

theorem admitted_action_is_supported_or_baseline
    (certificate : TreeActionCertificate)
    (accepted : certificate.admissible = true) :
    certificate.minimumSupport ≤ certificate.supportCount ∨
      certificate.isBaseline = true := by
  have facts := (by simpa [admissible] using accepted :
    certificate.safe = true ∧
      (certificate.minimumSupport ≤ certificate.supportCount ∨
        certificate.isBaseline = true))
  exact facts.2

end TreeActionCertificate

/-- Certificate that the selected pessimistic lower value dominates every
    alternative retained by the trusted finite tree language. -/
structure SafeTreeSelectionCertificate where
  selected : TreeActionCertificate
  alternatives : List Int
  selectedAdmissible : selected.admissible = true
  dominates : ∀ value, value ∈ alternatives → value ≤ selected.lowerValue
  deriving Repr

namespace SafeTreeSelectionCertificate

theorem selected_action_is_safe
    (certificate : SafeTreeSelectionCertificate) :
    certificate.selected.safe = true :=
  certificate.selected.admitted_action_is_safe
    certificate.selectedAdmissible

theorem selected_action_respects_baseline_constraint
    (certificate : SafeTreeSelectionCertificate) :
    certificate.selected.minimumSupport ≤ certificate.selected.supportCount ∨
      certificate.selected.isBaseline = true :=
  certificate.selected.admitted_action_is_supported_or_baseline
    certificate.selectedAdmissible

theorem selected_dominates_registered_alternatives
    (certificate : SafeTreeSelectionCertificate)
    (value : Int)
    (member : value ∈ certificate.alternatives) :
    value ≤ certificate.selected.lowerValue :=
  certificate.dominates value member

end SafeTreeSelectionCertificate

end LeanFinance.Control
