import LeanFinance.Types

namespace LeanFinance.SupplyChain

/-- Heterogeneous entities that may appear in an industrial production graph. -/
inductive NodeKind where
  | company
  | facility
  | process
  | technology
  | resource
  | product
  | qualification
  deriving Repr, DecidableEq

/-- Semantic edge classes for a multilayer industrial network. -/
inductive EdgeKind where
  | materialFlow
  | dependency
  | substitution
  | qualification
  | ownership
  | contract
  | commonFailureDomain
  deriving Repr, DecidableEq

/-- Directed, weighted relation in a multilayer industrial graph. Integer
    weights are exact scaled observations supplied by empirical adapters. -/
structure IndustrialEdge where
  id : Nat
  source : Nat
  target : Nat
  kind : EdgeKind
  capacity : Nat
  leadTime : Time
  dependencyWeight : Nat
  substitutionWeight : Nat
  switchingCost : Nat
  deriving Repr, DecidableEq

/-- A topology-only view deliberately excludes capacities and economic terms.
    It is used to state precisely that topology cannot determine bottlenecks. -/
structure TopologySignature where
  upstream : List Nat
  downstream : List Nat
  deriving Repr, DecidableEq

/-- Announced capacity is counted only after both physical completion and
    customer or regulatory qualification. -/
structure CapacityAddition where
  units : Nat
  completionTime : Time
  qualificationTime : Time
  deriving Repr, DecidableEq

namespace CapacityAddition

/-- The project is usable at `t` only after construction and qualification. -/
def ReadyAt (project : CapacityAddition) (t : Time) : Prop :=
  project.completionTime <= t ∧ project.qualificationTime <= t

/-- Effective, rather than nameplate, capacity contributed at time `t`. -/
def capacityAt (project : CapacityAddition) (t : Time) : Nat :=
  if project.ReadyAt t then project.units else 0

theorem capacityAt_eq_units_of_ready
    (project : CapacityAddition)
    (t : Time)
    (ready : project.ReadyAt t) :
    project.capacityAt t = project.units := by
  simp [capacityAt, ready]

theorem capacityAt_eq_zero_of_not_ready
    (project : CapacityAddition)
    (t : Time)
    (notReady : ¬ project.ReadyAt t) :
    project.capacityAt t = 0 := by
  simp [capacityAt, notReady]

end CapacityAddition

/-- A technically plausible alternate supplier may still be unusable because
    completion, qualification, switching, or IP compatibility is missing. -/
structure AlternateSupply where
  units : Nat
  physicalReadyTime : Time
  qualificationTime : Time
  switchingReadyTime : Time
  ipCompatible : Bool
  deriving Repr, DecidableEq

namespace AlternateSupply

/-- Horizon-dependent effective substitutability. -/
def UsableAt (supply : AlternateSupply) (t : Time) : Prop :=
  supply.physicalReadyTime <= t ∧
  supply.qualificationTime <= t ∧
  supply.switchingReadyTime <= t ∧
  supply.ipCompatible = true

def capacityAt (supply : AlternateSupply) (t : Time) : Nat :=
  if supply.UsableAt t then supply.units else 0

theorem capacityAt_eq_units_of_usable
    (supply : AlternateSupply)
    (t : Time)
    (usable : supply.UsableAt t) :
    supply.capacityAt t = supply.units := by
  simp [capacityAt, usable]

theorem capacityAt_eq_zero_of_not_usable
    (supply : AlternateSupply)
    (t : Time)
    (notUsable : ¬ supply.UsableAt t) :
    supply.capacityAt t = 0 := by
  simp [capacityAt, notUsable]

theorem capacityAt_eq_zero_of_ip_incompatible
    (supply : AlternateSupply)
    (t : Time)
    (incompatible : supply.ipCompatible = false) :
    supply.capacityAt t = 0 := by
  simp [capacityAt, UsableAt, incompatible]

end AlternateSupply

/-- Total qualified capacity from a list of expansion projects. -/
def additionsCapacityAt : List CapacityAddition → Time → Nat
  | [], _ => 0
  | project :: rest, t =>
      project.capacityAt t + additionsCapacityAt rest t

/-- Total qualified and switch-ready alternate capacity. -/
def alternatesCapacityAt : List AlternateSupply → Time → Nat
  | [], _ => 0
  | supply :: rest, t =>
      supply.capacityAt t + alternatesCapacityAt rest t

/-- A local process node in a capacity-constrained production network.
    `inputUnitsPerOutput` maps final demand into required flow through the node. -/
structure SupplyNode where
  id : Nat
  kind : NodeKind
  topology : TopologySignature
  incumbentCapacity : Nat
  inputUnitsPerOutput : Nat
  additions : List CapacityAddition
  alternates : List AlternateSupply
  deriving Repr, DecidableEq

/-- A directed, weighted industrial network with heterogeneous local nodes. -/
structure IndustrialNetwork where
  nodes : List SupplyNode
  edges : List IndustrialEdge
  deriving Repr, DecidableEq

/-- Required node flow induced by final demand. -/
def requiredFlow (node : SupplyNode) (finalDemand : Nat) : Nat :=
  node.inputUnitsPerOutput * finalDemand

/-- Capacity usable by time `t`, including qualified additions and substitutes. -/
def effectiveCapacityAt (node : SupplyNode) (t : Time) : Nat :=
  additionsCapacityAt node.additions t +
    (alternatesCapacityAt node.alternates t + node.incumbentCapacity)

/-- A physical capacity bottleneck is a strictly binding capacity constraint. -/
def IsCapacityBottleneckAt
    (node : SupplyNode)
    (t : Time)
    (finalDemand : Nat) : Prop :=
  effectiveCapacityAt node t < requiredFlow node finalDemand

/-- Capacity sufficiency is the exact negating inequality used by certificates. -/
def CapacitySufficientAt
    (node : SupplyNode)
    (t : Time)
    (finalDemand : Nat) : Prop :=
  requiredFlow node finalDemand <= effectiveCapacityAt node t

/-- Units of unmet required flow at a node. -/
def scarcityUnitsAt
    (node : SupplyNode)
    (t : Time)
    (finalDemand : Nat) : Nat :=
  requiredFlow node finalDemand - effectiveCapacityAt node t

theorem not_capacityBottleneck_of_sufficient
    (node : SupplyNode)
    (t : Time)
    (finalDemand : Nat)
    (sufficient : CapacitySufficientAt node t finalDemand) :
    ¬ IsCapacityBottleneckAt node t finalDemand :=
  not_lt_of_ge sufficient

theorem scarcityUnitsAt_eq_zero_of_sufficient
    (node : SupplyNode)
    (t : Time)
    (finalDemand : Nat)
    (sufficient : CapacitySufficientAt node t finalDemand) :
    scarcityUnitsAt node t finalDemand = 0 := by
  unfold scarcityUnitsAt
  exact Nat.sub_eq_zero_of_le sufficient

theorem effectiveCapacityAt_with_ready_addition
    (node : SupplyNode)
    (project : CapacityAddition)
    (t : Time)
    (ready : project.ReadyAt t) :
    effectiveCapacityAt
      { node with additions := project :: node.additions } t =
      project.units + effectiveCapacityAt node t := by
  simp [effectiveCapacityAt, additionsCapacityAt,
    CapacityAddition.capacityAt, ready, Nat.add_assoc]

end LeanFinance.SupplyChain
