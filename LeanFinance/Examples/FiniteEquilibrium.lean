import LeanFinance.Certificate.EquilibriumCertificate

namespace LeanFinance.Examples

open GameTheory Certificate

def toyPlayer : Player :=
  {
    id := 0
    kind := .marketMaker
    riskAversion := 0
    leverageLimit := 1
    horizon := 1
  }

def toyProfile : StrategyProfile :=
  fun _ => .hold

def toyPayoff : Payoff :=
  { utility := fun _ _ => 0 }

def toyFiniteGame : FiniteGame :=
  {
    players := [toyPlayer]
    actions := fun _ => [.hold]
    payoff := toyPayoff
  }

def toyEquilibriumCertificate :
    FiniteEquilibriumCertificate toyFiniteGame :=
  {
    profile := toyProfile
    profileAdmissible := by
      intro player playerMember
      simp at playerMember
      subst player
      simp [toyFiniteGame, toyProfile]
    noProfitableDeviation := by
      intro player playerMember alternative alternativeMember
      simp at playerMember
      subst player
      simp [toyFiniteGame, toyPayoff, Payoff.deviationUtility]
  }

example : FiniteNashEquilibrium
    toyFiniteGame toyEquilibriumCertificate.profile :=
  toyEquilibriumCertificate.sound

end LeanFinance.Examples
