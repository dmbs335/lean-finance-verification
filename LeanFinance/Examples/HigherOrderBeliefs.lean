import LeanFinance.GameTheory.HigherOrderBeliefs

namespace LeanFinance.Examples

open GameTheory

def beliefA : Belief :=
  {
    playerId := 0
    fundamentalExpectation := 10
    marketExpectation := 12
    higherOrderExpectation := 15
    confidence := 1
  }

def beliefB : Belief :=
  {
    playerId := 1
    fundamentalExpectation := 10
    marketExpectation := 3
    higherOrderExpectation := -4
    confidence := 1
  }

example :
    beautyContestSignal zeroCoordination beliefA =
      beliefA.fundamentalExpectation :=
  beautyContestSignal_zeroCoordination beliefA

example :
    beautyContestSignal fullCoordination beliefA =
      beliefA.higherOrderExpectation :=
  beautyContestSignal_fullCoordination beliefA

/-- At zero coordination, two players with the same B1 produce the same signal
    even when B2 and B3 differ. -/
example :
    beautyContestSignal zeroCoordination beliefA =
      beautyContestSignal zeroCoordination beliefB :=
  zeroCoordination_dependsOnlyOnFundamental beliefA beliefB rfl

end LeanFinance.Examples
