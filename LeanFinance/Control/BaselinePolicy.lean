import LeanFinance.Control.Shield

namespace LeanFinance.Control

abbrev DeterministicPolicy (State Action : Type) := State → Action

/-- Logged support for one state-action pair. -/
structure SupportTable (State Action : Type) where
  count : State → Action → Nat

namespace SupportTable

def Supported
    (table : SupportTable State Action)
    (minimumCount : Nat)
    (state : State)
    (action : Action) : Prop :=
  minimumCount ≤ table.count state action

end SupportTable

/-- SPIBB-style baseline restriction: if the candidate's chosen action lacks
    support, the candidate must agree with the trusted baseline at that state. -/
def RespectsBaseline
    (table : SupportTable State Action)
    (minimumCount : Nat)
    (baseline candidate : DeterministicPolicy State Action) : Prop :=
  ∀ state,
    ¬ table.Supported minimumCount state (candidate state) →
      candidate state = baseline state

/-- At every state the candidate action is supported or is exactly the baseline
    action. -/
theorem supported_or_baseline
    (table : SupportTable State Action)
    (minimumCount : Nat)
    (baseline candidate : DeterministicPolicy State Action)
    (respects : RespectsBaseline table minimumCount baseline candidate)
    (state : State) :
    table.Supported minimumCount state (candidate state) ∨
      candidate state = baseline state := by
  by_cases supported :
      table.Supported minimumCount state (candidate state)
  · exact Or.inl supported
  · exact Or.inr (respects state supported)

/-- Arithmetic certificate for a pessimistic baseline-relative improvement.
    Statistical validity of the lower bounds is a separate declared obligation. -/
structure PessimisticValueCertificate where
  baselineLower : Int
  candidateLower : Int
  requiredMargin : Int
  improvement : baselineLower + requiredMargin ≤ candidateLower
  deriving Repr

namespace PessimisticValueCertificate

theorem candidate_meets_registered_margin
    (certificate : PessimisticValueCertificate) :
    certificate.baselineLower + certificate.requiredMargin ≤
      certificate.candidateLower :=
  certificate.improvement

end PessimisticValueCertificate

/-- Proof-carrying deterministic policy candidate. -/
structure SafePolicyCertificate (State Action : Type) where
  baseline : DeterministicPolicy State Action
  candidate : DeterministicPolicy State Action
  support : SupportTable State Action
  minimumCount : Nat
  respectsBaseline :
    RespectsBaseline support minimumCount baseline candidate
  admissible : State → Action → Prop
  candidateSafe : ∀ state, admissible state (candidate state)
  value : PessimisticValueCertificate

namespace SafePolicyCertificate

theorem certified_candidate_is_safe
    (certificate : SafePolicyCertificate State Action)
    (state : State) :
    certificate.admissible state (certificate.candidate state) :=
  certificate.candidateSafe state

end SafePolicyCertificate

end LeanFinance.Control
