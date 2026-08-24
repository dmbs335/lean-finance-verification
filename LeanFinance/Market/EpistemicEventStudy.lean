namespace LeanFinance.Market

/-- Three registered withdrawal observations around one evidence-domain event. -/
structure WithdrawalWindow where
  baseline : Int
  preEvent : Int
  postEvent : Int
  deriving Repr

def preTrendChange (window : WithdrawalWindow) : Int :=
  window.preEvent - window.baseline

def eventChange (window : WithdrawalWindow) : Int :=
  window.postEvent - window.preEvent

/-- Matched difference-in-differences on withdrawal rates. -/
def eventDifferenceInDifferences
    (treated control : WithdrawalWindow) : Int :=
  eventChange treated - eventChange control

/-- If the exposed strategy's event-window change exceeds its matched control,
    the registered difference-in-differences is positive. -/
theorem positive_did_of_larger_treated_event_change
    (treated control : WithdrawalWindow)
    (larger : eventChange control < eventChange treated) :
    0 < eventDifferenceInDifferences treated control := by
  exact Int.sub_pos.mpr larger

/-- A normalized bounded event-study certificate. The propositions state only
    that the registered matching, pre-trend, and event-effect gates passed. -/
structure EpistemicEventStudyCertificate where
  planDigest : String
  pairCount : Nat
  eventDidNumerator : Int
  eventDidDenominator : Nat
  preregistrationPassed : Bool
  matchingPassed : Bool
  preTrendPassed : Bool
  eventEffectPassed : Bool
  gateProof :
    preregistrationPassed = true ∧
      matchingPassed = true ∧
        preTrendPassed = true ∧
          eventEffectPassed = true

namespace EpistemicEventStudyCertificate

theorem all_registered_gates_pass
    (certificate : EpistemicEventStudyCertificate) :
    certificate.preregistrationPassed = true ∧
      certificate.matchingPassed = true ∧
        certificate.preTrendPassed = true ∧
          certificate.eventEffectPassed = true :=
  certificate.gateProof

end EpistemicEventStudyCertificate

end LeanFinance.Market
