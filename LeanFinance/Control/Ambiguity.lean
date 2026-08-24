namespace LeanFinance.Control

/-- A lower bound that holds for every model still admissible under the current
    evidence state. -/
def LowerBoundOn
    (models : List Model)
    (value : Model → Int)
    (bound : Int) : Prop :=
  ∀ model,
    model ∈ models → bound ≤ value model

/-- Greatest represented lower bound over one finite ambiguity set. -/
def GreatestLowerBound
    (models : List Model)
    (value : Model → Int)
    (bound : Int) : Prop :=
  LowerBoundOn models value bound ∧
    ∀ candidate,
      LowerBoundOn models value candidate → candidate ≤ bound

/-- Stronger evidence removes models. The robust lower value therefore cannot
    decrease when both old and refined values are greatest lower bounds. -/
theorem evidence_refinement_improves_robust_lower_bound
    (outer inner : List Model)
    (value : Model → Int)
    (outerLower innerLower : Int)
    (refines : ∀ model, model ∈ inner → model ∈ outer)
    (outerGreatest : GreatestLowerBound outer value outerLower)
    (innerGreatest : GreatestLowerBound inner value innerLower) :
    outerLower ≤ innerLower := by
  apply innerGreatest.2
  intro model member
  exact outerGreatest.1 model (refines model member)

end LeanFinance.Control
