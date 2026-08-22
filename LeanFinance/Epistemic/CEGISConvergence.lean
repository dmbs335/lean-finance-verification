namespace LeanFinance.Epistemic

universe u v

/-- A finite constraint-based synthesis problem. Constraints may be terminal
    history-pair separator edges, first-violation transition classes, fault
    scenarios, or a product of these obligations. -/
structure FiniteSynthesisProblem (Constraint : Type u) (Candidate : Type v) where
  constraints : List Constraint
  satisfies : Candidate → Constraint → Prop
  cost : Candidate → Nat

namespace FiniteSynthesisProblem

/-- One candidate satisfies every constraint in an explicit list. -/
def SatisfiesAll
    {Constraint : Type u}
    {Candidate : Type v}
    (problem : FiniteSynthesisProblem Constraint Candidate)
    (candidate : Candidate)
    (constraints : List Constraint) : Prop :=
  ∀ constraint,
    constraint ∈ constraints →
      problem.satisfies candidate constraint

/-- Satisfying a larger constraint list implies satisfying every included
    restriction. -/
theorem satisfiesAll_of_subset
    {Constraint : Type u}
    {Candidate : Type v}
    (problem : FiniteSynthesisProblem Constraint Candidate)
    (candidate : Candidate)
    (small large : List Constraint)
    (included : ∀ constraint, constraint ∈ small → constraint ∈ large)
    (satisfiesLarge : problem.SatisfiesAll candidate large) :
    problem.SatisfiesAll candidate small := by
  intro constraint member
  exact satisfiesLarge constraint (included constraint member)

end FiniteSynthesisProblem

/-- An exact master result for the currently discovered constraints. -/
def ExactMasterResult
    {Constraint : Type u}
    {Candidate : Type v}
    (problem : FiniteSynthesisProblem Constraint Candidate)
    (known : List Constraint)
    (selected : Candidate) : Prop :=
  problem.SatisfiesAll selected known ∧
    ∀ candidate,
      problem.SatisfiesAll candidate known →
        problem.cost selected ≤ problem.cost candidate

/-- The result of a complete counterexample oracle. -/
inductive OracleOutcome (Constraint : Type u) where
  | verified
  | counterexample (constraint : Constraint)

/-- A complete oracle either certifies all declared constraints or returns one
    actual violated constraint from the finite problem universe. -/
def OracleOutcome.Valid
    {Constraint : Type u}
    {Candidate : Type v}
    (problem : FiniteSynthesisProblem Constraint Candidate)
    (candidate : Candidate) :
    OracleOutcome Constraint → Prop
  | .verified =>
      problem.SatisfiesAll candidate problem.constraints
  | .counterexample constraint =>
      constraint ∈ problem.constraints ∧
        ¬ problem.satisfies candidate constraint

/-- One proof-carrying CEGIS refinement round. The exact master solves all known
    constraints; the complete oracle returns a fresh violated constraint; and
    the next master problem prepends precisely that constraint. -/
structure ConstraintCEGISRound
    {Constraint : Type u}
    {Candidate : Type v}
    (problem : FiniteSynthesisProblem Constraint Candidate) where
  knownBefore : List Constraint
  candidate : Candidate
  masterExact :
    ExactMasterResult problem knownBefore candidate
  counterexample : Constraint
  oracleValid :
    (OracleOutcome.counterexample counterexample).Valid
      problem candidate
  fresh : counterexample ∉ knownBefore
  knownAfter : List Constraint
  afterEq : knownAfter = counterexample :: knownBefore

namespace ConstraintCEGISRound

/-- Every counterexample round strictly increases the discovered constraint
    list by one. -/
theorem knownAfter_length
    {Constraint : Type u}
    {Candidate : Type v}
    {problem : FiniteSynthesisProblem Constraint Candidate}
    (round : ConstraintCEGISRound problem) :
    round.knownAfter.length = round.knownBefore.length + 1 := by
  rw [round.afterEq]
  simp

/-- The oracle's counterexample is a declared synthesis obligation. -/
theorem counterexample_mem_problem
    {Constraint : Type u}
    {Candidate : Type v}
    {problem : FiniteSynthesisProblem Constraint Candidate}
    (round : ConstraintCEGISRound problem) :
    round.counterexample ∈ problem.constraints :=
  round.oracleValid.1

/-- The exact-master candidate genuinely fails the fresh oracle constraint. -/
theorem candidate_fails_counterexample
    {Constraint : Type u}
    {Candidate : Type v}
    {problem : FiniteSynthesisProblem Constraint Candidate}
    (round : ConstraintCEGISRound problem) :
    ¬ problem.satisfies round.candidate round.counterexample :=
  round.oracleValid.2

end ConstraintCEGISRound

/-- A structural certificate that one natural-number measure decreases after
    every CEGIS counterexample round. The measure can be instantiated as the
    number of undiscovered finite constraints. -/
inductive StrictlyDecreasingMeasures : Nat → List Nat → Prop where
  | nil (start : Nat) : StrictlyDecreasingMeasures start []
  | cons
      {start next : Nat}
      {rest : List Nat}
      (progress : next < start)
      (tail : StrictlyDecreasingMeasures next rest) :
      StrictlyDecreasingMeasures start (next :: rest)

namespace StrictlyDecreasingMeasures

/-- A strictly decreasing natural measure bounds the number of refinement
    rounds by its initial value. -/
theorem length_le_start
    {start : Nat}
    {measures : List Nat}
    (decreasing : StrictlyDecreasingMeasures start measures) :
    measures.length ≤ start := by
  induction decreasing with
  | nil start =>
      simp
  | cons progress tail inductionHypothesis =>
      have restBelowStart :
          measures.length < start :=
        Nat.lt_of_le_of_lt inductionHypothesis progress
      simpa using Nat.succ_le_of_lt restBelowStart

/-- No proof-carrying run can contain more counterexample rounds than a finite
    initial undiscovered-constraint measure permits. -/
theorem no_run_longer_than_initial_measure
    {start : Nat}
    {measures : List Nat}
    (decreasing : StrictlyDecreasingMeasures start measures)
    (tooLong : start < measures.length) : False :=
  (Nat.not_lt_of_ge decreasing.length_le_start) tooLong

end StrictlyDecreasingMeasures

/-- A converged exact CEGIS certificate. The final oracle establishes global
    feasibility; the final master establishes minimum cost on discovered
    constraints; and every discovered constraint belongs to the complete
    finite universe. Consequently every globally feasible candidate was also
    feasible for the final master problem. -/
structure ConvergedCEGISCertificate
    {Constraint : Type u}
    {Candidate : Type v}
    (problem : FiniteSynthesisProblem Constraint Candidate) where
  discovered : List Constraint
  discoveredSubset :
    ∀ constraint,
      constraint ∈ discovered →
        constraint ∈ problem.constraints
  finalCandidate : Candidate
  finalMaster :
    ExactMasterResult problem discovered finalCandidate
  finalOracle :
    (OracleOutcome.verified : OracleOutcome Constraint).Valid
      problem finalCandidate
  initialMeasure : Nat
  afterMeasures : List Nat
  measuresDecrease :
    StrictlyDecreasingMeasures initialMeasure afterMeasures
  roundCount : Nat
  roundCountEq : roundCount = afterMeasures.length

namespace ConvergedCEGISCertificate

/-- A converged complete oracle proves that the final candidate satisfies the
    entire finite synthesis problem. -/
theorem final_sound
    {Constraint : Type u}
    {Candidate : Type v}
    {problem : FiniteSynthesisProblem Constraint Candidate}
    (certificate : ConvergedCEGISCertificate problem) :
    problem.SatisfiesAll
      certificate.finalCandidate problem.constraints :=
  certificate.finalOracle

/-- Exact-master optimality on discovered constraints plus a complete verified
    oracle implies global minimum cost over all fully feasible candidates. -/
theorem final_globally_optimal
    {Constraint : Type u}
    {Candidate : Type v}
    {problem : FiniteSynthesisProblem Constraint Candidate}
    (certificate : ConvergedCEGISCertificate problem)
    (candidate : Candidate)
    (globallyFeasible :
      problem.SatisfiesAll candidate problem.constraints) :
    problem.cost certificate.finalCandidate ≤
      problem.cost candidate := by
  apply certificate.finalMaster.2 candidate
  exact problem.satisfiesAll_of_subset
    candidate certificate.discovered problem.constraints
    certificate.discoveredSubset globallyFeasible

/-- The proof-carrying convergence transcript cannot exceed its finite initial
    counterexample measure. -/
theorem rounds_bounded
    {Constraint : Type u}
    {Candidate : Type v}
    {problem : FiniteSynthesisProblem Constraint Candidate}
    (certificate : ConvergedCEGISCertificate problem) :
    certificate.roundCount ≤ certificate.initialMeasure := by
  rw [certificate.roundCountEq]
  exact certificate.measuresDecrease.length_le_start

end ConvergedCEGISCertificate

end LeanFinance.Epistemic
