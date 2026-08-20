import LeanFinance.SupplyChain.Network

namespace LeanFinance.SupplyChain

/-- Economic and physical causes that may instantiate a binding constraint. -/
inductive BottleneckKind where
  | capacity
  | yield
  | technological
  | geographic
  | supplierConcentration
  | temporal
  | regulatory
  | capital
  | knowledge
  | switching
  | logistics
  | coordination
  deriving Repr, DecidableEq

/-- A small serializable claim whose inequality can be checked by computation. -/
structure BottleneckClaim where
  kind : BottleneckKind
  nodeId : Nat
  decisionTime : Timestamp
  available : Nat
  required : Nat
  deriving Repr, DecidableEq

namespace BottleneckClaim

/-- The claim is valid exactly when the represented constraint is binding. -/
def Valid (claim : BottleneckClaim) : Prop :=
  claim.available < claim.required

/-- Decidable checker used at the empirical/formal boundary. -/
def check (claim : BottleneckClaim) : Bool :=
  decide claim.Valid

theorem check_eq_true_iff_valid (claim : BottleneckClaim) :
    claim.check = true ↔ claim.Valid := by
  simp [check, Valid]

theorem check_sound
    (claim : BottleneckClaim)
    (accepted : claim.check = true) :
    claim.Valid :=
  (check_eq_true_iff_valid claim).mp accepted

end BottleneckClaim

/-- Materialize a claim from a dynamically evaluated supply node. -/
def claimOfNode
    (kind : BottleneckKind)
    (node : SupplyNode)
    (t : Timestamp)
    (finalDemand : Nat) : BottleneckClaim :=
  {
    kind := kind
    nodeId := node.id
    decisionTime := t
    available := effectiveCapacityAt node t
    required := requiredFlow node finalDemand
  }

theorem claimOfNode_valid_iff
    (kind : BottleneckKind)
    (node : SupplyNode)
    (t : Timestamp)
    (finalDemand : Nat) :
    (claimOfNode kind node t finalDemand).Valid ↔
      IsCapacityBottleneckAt node t finalDemand := by
  rfl

/-- Scan order is explicit: the result is the first binding node in the supplied
    process order, not a centrality ranking. -/
def firstBottleneckAt : List SupplyNode → Timestamp → Nat → Option Nat
  | [], _, _ => none
  | node :: rest, t, finalDemand =>
      if IsCapacityBottleneckAt node t finalDemand then
        some node.id
      else
        firstBottleneckAt rest t finalDemand

/-- A successful scan result always names an actual binding node in the list. -/
theorem firstBottleneckAt_sound
    (nodes : List SupplyNode)
    (t : Timestamp)
    (finalDemand nodeId : Nat)
    (found : firstBottleneckAt nodes t finalDemand = some nodeId) :
    ∃ node, node ∈ nodes ∧ node.id = nodeId ∧
      IsCapacityBottleneckAt node t finalDemand := by
  induction nodes with
  | nil =>
      simp [firstBottleneckAt] at found
  | cons head tail ih =>
      by_cases binding : IsCapacityBottleneckAt head t finalDemand
      · have idMatches : head.id = nodeId := by
          simpa [firstBottleneckAt, binding] using found
        exact ⟨head, by simp, idMatches, binding⟩
      · have foundInTail :
            firstBottleneckAt tail t finalDemand = some nodeId := by
          simpa [firstBottleneckAt, binding] using found
        obtain ⟨node, member, idMatches, nodeBinding⟩ :=
          ih foundInTail
        exact ⟨node, List.mem_cons_of_mem head member,
          idMatches, nodeBinding⟩

/-- Integer-scaled inputs for a dynamic bottleneck rent score. Capture and
    ownership may be represented in basis points; the common scale factor is
    intentionally retained so certification does not require rounding. -/
structure DynamicRentInput where
  scarcityUnits : Nat
  duration : Nat
  nonSubstitutionWeight : Nat
  captureWeight : Nat
  ownershipWeight : Nat
  pricedScaledRent : Nat
  deriving Repr, DecidableEq

/-- Physical scarcity before bargaining and ownership allocation. -/
def physicalScarcityScore (input : DynamicRentInput) : Nat :=
  input.scarcityUnits * input.duration * input.nonSubstitutionWeight

/-- Scarcity rent that the represented firm can economically capture. -/
def scaledCapturedRent (input : DynamicRentInput) : Nat :=
  physicalScarcityScore input * input.captureWeight * input.ownershipWeight

/-- Investable score after subtracting scarcity rent already embedded in price. -/
def investableGap (input : DynamicRentInput) : Nat :=
  scaledCapturedRent input - input.pricedScaledRent

/-- Construct score inputs from the network-computed scarcity quantity. -/
def rentInputOfNode
    (node : SupplyNode)
    (t : Timestamp)
    (finalDemand duration nonSubstitutionWeight captureWeight
      ownershipWeight pricedScaledRent : Nat) : DynamicRentInput :=
  {
    scarcityUnits := scarcityUnitsAt node t finalDemand
    duration := duration
    nonSubstitutionWeight := nonSubstitutionWeight
    captureWeight := captureWeight
    ownershipWeight := ownershipWeight
    pricedScaledRent := pricedScaledRent
  }

theorem physicalScarcityScore_eq_zero_of_zero_scarcity
    (input : DynamicRentInput)
    (zeroScarcity : input.scarcityUnits = 0) :
    physicalScarcityScore input = 0 := by
  simp [physicalScarcityScore, zeroScarcity]

theorem physicalScarcityScore_eq_zero_of_zero_duration
    (input : DynamicRentInput)
    (zeroDuration : input.duration = 0) :
    physicalScarcityScore input = 0 := by
  simp [physicalScarcityScore, zeroDuration]

theorem scaledCapturedRent_eq_zero_of_zero_capture
    (input : DynamicRentInput)
    (zeroCapture : input.captureWeight = 0) :
    scaledCapturedRent input = 0 := by
  simp [scaledCapturedRent, zeroCapture]

theorem scaledCapturedRent_eq_zero_of_zero_ownership
    (input : DynamicRentInput)
    (zeroOwnership : input.ownershipWeight = 0) :
    scaledCapturedRent input = 0 := by
  simp [scaledCapturedRent, zeroOwnership]

theorem investableGap_eq_zero_of_fully_priced
    (input : DynamicRentInput)
    (fullyPriced : scaledCapturedRent input ≤ input.pricedScaledRent) :
    investableGap input = 0 := by
  unfold investableGap
  exact Nat.sub_eq_zero_of_le fullyPriced

theorem physicalScarcityScore_eq_zero_of_capacity_sufficient
    (node : SupplyNode)
    (t : Timestamp)
    (finalDemand duration nonSubstitutionWeight captureWeight
      ownershipWeight pricedScaledRent : Nat)
    (sufficient : CapacitySufficientAt node t finalDemand) :
    physicalScarcityScore
      (rentInputOfNode node t finalDemand duration nonSubstitutionWeight
        captureWeight ownershipWeight pricedScaledRent) = 0 := by
  have zeroScarcity : scarcityUnitsAt node t finalDemand = 0 :=
    scarcityUnitsAt_eq_zero_of_sufficient node t finalDemand sufficient
  simp [rentInputOfNode, physicalScarcityScore, zeroScarcity]

/-- Two nodes can have identical graph topology and input intensity while one
    binds and the other does not. Capacities therefore cannot be replaced by a
    topology-only centrality statistic. -/
def topologyWitness : TopologySignature :=
  { upstream := [10, 11], downstream := [20, 21] }

def tightTopologyNode : SupplyNode :=
  {
    id := 1
    kind := .process
    topology := topologyWitness
    incumbentCapacity := 5
    inputUnitsPerOutput := 1
    additions := []
    alternates := []
  }

def slackTopologyNode : SupplyNode :=
  {
    id := 2
    kind := .process
    topology := topologyWitness
    incumbentCapacity := 20
    inputUnitsPerOutput := 1
    additions := []
    alternates := []
  }

theorem topology_alone_does_not_determine_bottleneck :
    tightTopologyNode.topology = slackTopologyNode.topology ∧
    IsCapacityBottleneckAt tightTopologyNode 0 10 ∧
    ¬ IsCapacityBottleneckAt slackTopologyNode 0 10 := by
  constructor
  · rfl
  constructor
  · decide
  · decide

end LeanFinance.SupplyChain
