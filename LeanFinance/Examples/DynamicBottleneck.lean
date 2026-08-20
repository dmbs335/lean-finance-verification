import LeanFinance.SupplyChain.Certificate

namespace LeanFinance.Examples

open Backtest SupplyChain

/-- A stylized HBM or advanced-packaging expansion: physically complete at
    time 4, but not customer-qualified until time 6. -/
def hbmExpansion : CapacityAddition :=
  {
    units := 30
    completionTime := 4
    qualificationTime := 6
  }

def hbmNode : SupplyNode :=
  {
    id := 100
    kind := .process
    topology :=
      { upstream := [1, 2], downstream := [200] }
    incumbentCapacity := 80
    inputUnitsPerOutput := 1
    additions := [hbmExpansion]
    alternates := []
  }

example : hbmExpansion.capacityAt 5 = 0 := by
  decide

example : hbmExpansion.capacityAt 6 = 30 := by
  decide

/-- The announced project cannot relieve the shortage before qualification. -/
example : IsCapacityBottleneckAt hbmNode 5 100 := by
  decide

/-- Once qualified, effective capacity exceeds required flow. -/
example : ¬ IsCapacityBottleneckAt hbmNode 6 100 := by
  decide

example : scarcityUnitsAt hbmNode 5 100 = 20 := by
  decide

example : scarcityUnitsAt hbmNode 6 100 = 0 := by
  decide

example : firstBottleneckAt [hbmNode] 5 100 = some hbmNode.id := by
  decide

def bottleneckDataset : Dataset :=
  {
    id := "hbm-capacity-snapshot"
    observedAt := 4
    availableAt := 5
    contentHash := "sha256:hbm-capacity"
  }

def bottleneckDecision : Decision :=
  {
    strategyId := "dynamic-bottleneck-score"
    decisionTime := 5
    datasets := [bottleneckDataset]
    features := []
    parameterHash := "sha256:dynamic-bottleneck-parameters"
  }

def hbmBottleneckCertificate :
    DynamicBottleneckCertificate hbmNode bottleneckDecision 100 :=
  {
    noFutureInformation := by
      constructor
      · intro dataset used
        have datasetMatches : dataset = bottleneckDataset := by
          simpa [bottleneckDecision] using used
        subst dataset
        decide
      · intro feature used
        simp [bottleneckDecision] at used
    binding := by decide
  }

example :
    (claimOfNode BottleneckKind.capacity hbmNode
      bottleneckDecision.decisionTime 100).check = true :=
  DynamicBottleneckCertificate.claimChecks
    hbmNode bottleneckDecision 100 hbmBottleneckCertificate

/-- Physical scarcity need not become private rent when price capture is zero,
    as in a regulated or fixed-price shortage. -/
def regulatedShortage : DynamicRentInput :=
  {
    scarcityUnits := 20
    duration := 4
    nonSubstitutionWeight := 10
    captureWeight := 0
    ownershipWeight := 10000
    pricedScaledRent := 0
  }

example : scaledCapturedRent regulatedShortage = 0 :=
  scaledCapturedRent_eq_zero_of_zero_capture regulatedShortage rfl

/-- Even captured rent supplies no investable gap when already fully priced. -/
def fullyPricedShortage : DynamicRentInput :=
  {
    scarcityUnits := 2
    duration := 3
    nonSubstitutionWeight := 4
    captureWeight := 5
    ownershipWeight := 6
    pricedScaledRent := 720
  }

example : investableGap fullyPricedShortage = 0 := by
  decide

/-- A high-growth, highly connected process can still have no scarcity when
    capacity is ample, a stylized battery-cell negative control. -/
def overcapacityNode : SupplyNode :=
  {
    id := 300
    kind := .process
    topology := topologyWitness
    incumbentCapacity := 300
    inputUnitsPerOutput := 1
    additions := []
    alternates := []
  }

example : ¬ IsCapacityBottleneckAt overcapacityNode 0 100 := by
  decide

end LeanFinance.Examples
