import LeanFinance.GameTheory.FiniteGame

namespace LeanFinance.Certificate

open GameTheory

/-- A search procedure may propose a profile, but the certificate must carry
    proofs that it is admissible and has no profitable finite deviation. -/
structure FiniteEquilibriumCertificate (game : FiniteGame) where
  profile : StrategyProfile
  profileAdmissible : ProfileAdmissible game profile
  noProfitableDeviation :
    ∀ player, player ∈ game.players →
      FiniteIsBestResponse game player profile

theorem FiniteEquilibriumCertificate.sound
    {game : FiniteGame}
    (certificate : FiniteEquilibriumCertificate game) :
    FiniteNashEquilibrium game certificate.profile :=
  ⟨certificate.profileAdmissible, certificate.noProfitableDeviation⟩

theorem verifiedEquilibrium_noProfitableDeviation
    {game : FiniteGame}
    (certificate : FiniteEquilibriumCertificate game)
    {player : Player}
    (playerMember : player ∈ game.players)
    {alternative : Action}
    (alternativeMember : alternative ∈ game.actions player.id) :
    game.payoff.utility player certificate.profile >=
      game.payoff.deviationUtility
        player certificate.profile alternative :=
  certificate.noProfitableDeviation
    player playerMember alternative alternativeMember

end LeanFinance.Certificate
