namespace LeanFinance.Constraints

structure ShortState where
  shortPosition : Nat
  borrowAvailable : Nat
  marginSlack : Nat
  deriving Repr

def MustCover (state : ShortState) : Prop :=
  state.borrowAvailable < state.shortPosition ∨ state.marginSlack = 0

instance decidableMustCover (state : ShortState) : Decidable (MustCover state) := by
  unfold MustCover
  infer_instance

def ForcedCover (state : ShortState) : Nat :=
  if MustCover state then state.shortPosition else 0

theorem no_cover_trigger_no_forced_cover
    (state : ShortState)
    (h : ¬ MustCover state) :
    ForcedCover state = 0 := by
  simp [ForcedCover, h]

theorem cover_trigger_forces_cover
    (state : ShortState)
    (h : MustCover state) :
    ForcedCover state = state.shortPosition := by
  simp [ForcedCover, h]

end LeanFinance.Constraints
