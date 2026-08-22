import LeanFinance.Epistemic.Connectivity

namespace LeanFinance.Epistemic.ConnectivityExample

inductive History where
  | honest
  | attack
  deriving Repr, DecidableEq

inductive Channel where
  | receiptA
  | receiptB
  | receiptC
  deriving Repr, DecidableEq

inductive Observation where
  | clean
  | violation
  deriving Repr, DecidableEq

def observe : Channel → History → Observation
  | _, .honest => .clean
  | _, .attack => .violation

def claim : History → Prop
  | .honest => True
  | .attack => False

def selectedA : Channel → Prop
  | .receiptA => True
  | _ => False

def selectedAB : Channel → Prop
  | .receiptA | .receiptB => True
  | .receiptC => False

def selectedAC : Channel → Prop
  | .receiptA | .receiptC => True
  | .receiptB => False

/-- Any one uncompromised receipt suffices to separate the two histories. -/
theorem verifies_with_surviving_receipt
    {Fault : Type}
    (selected : Channel → Prop)
    (compromised : Fault → Channel → Prop)
    (fault : Fault)
    (receipt : Channel)
    (chosen : selected receipt)
    (survives : ¬ compromised fault receipt) :
    ChannelSelectionVerifies
      observe
      (SurvivingChannels selected compromised fault)
      claim := by
  intro left right sameEvidence
  cases left <;> cases right
  · exact Iff.rfl
  · have impossible :=
      sameEvidence receipt ⟨chosen, survives⟩
    simp [observe] at impossible
  · have impossible :=
      sameEvidence receipt ⟨chosen, survives⟩
    simp [observe] at impossible
  · exact Iff.rfl

inductive ChannelFault where
  | none
  | failA
  | failB
  | failC
  deriving Repr, DecidableEq

def compromisedChannel : ChannelFault → Channel → Prop
  | .none, _ => False
  | .failA, .receiptA => True
  | .failA, _ => False
  | .failB, .receiptB => True
  | .failB, _ => False
  | .failC, .receiptC => True
  | .failC, _ => False

def channelFaultRank : ChannelFault → Nat
  | .none => 0
  | _ => 1

/-- One receipt verifies in the no-fault case, so its connectivity is at least
one. -/
theorem single_receipt_connectivity_one :
    EvidenceConnectivityAtLeast
      observe selectedA claim
      compromisedChannel channelFaultRank 1 := by
  intro fault below
  cases fault with
  | none =>
      exact verifies_with_surviving_receipt
        selectedA compromisedChannel .none .receiptA
        (by simp [selectedA])
        (by simp [compromisedChannel])
  | failA => simp [channelFaultRank] at below
  | failB => simp [channelFaultRank] at below
  | failC => simp [channelFaultRank] at below

/-- The same selection cannot tolerate failure of its unique receipt. -/
theorem single_receipt_not_connectivity_two :
    ¬ EvidenceConnectivityAtLeast
      observe selectedA claim
      compromisedChannel channelFaultRank 2 := by
  intro connected
  have verified := connected .failA (by simp [channelFaultRank])
  have sameEvidence :
      ChannelsAgree observe
        (SurvivingChannels selectedA compromisedChannel .failA)
        .honest .attack := by
    intro evidenceChannel surviving
    cases evidenceChannel <;>
      simp [SurvivingChannels, selectedA, compromisedChannel] at surviving
  have equivalent := verified .honest .attack sameEvidence
  exact equivalent.mp True.intro

/-- Two independently failing channel instances tolerate every declared single
channel failure. -/
theorem two_receipts_connectivity_two :
    EvidenceConnectivityAtLeast
      observe selectedAB claim
      compromisedChannel channelFaultRank 2 := by
  intro fault _below
  cases fault with
  | none =>
      exact verifies_with_surviving_receipt
        selectedAB compromisedChannel .none .receiptA
        (by simp [selectedAB])
        (by simp [compromisedChannel])
  | failA =>
      exact verifies_with_surviving_receipt
        selectedAB compromisedChannel .failA .receiptB
        (by simp [selectedAB])
        (by simp [compromisedChannel])
  | failB =>
      exact verifies_with_surviving_receipt
        selectedAB compromisedChannel .failB .receiptA
        (by simp [selectedAB])
        (by simp [compromisedChannel])
  | failC =>
      exact verifies_with_surviving_receipt
        selectedAB compromisedChannel .failC .receiptA
        (by simp [selectedAB])
        (by simp [compromisedChannel])

inductive Domain where
  | providerX
  | providerY
  deriving Repr, DecidableEq

def domain : Channel → Domain
  | .receiptA | .receiptB => .providerX
  | .receiptC => .providerY

inductive DomainFault where
  | none
  | compromiseX
  | compromiseY
  deriving Repr, DecidableEq

def compromisedDomain : DomainFault → Domain → Prop
  | .none, _ => False
  | .compromiseX, .providerX => True
  | .compromiseX, .providerY => False
  | .compromiseY, .providerY => True
  | .compromiseY, .providerX => False

def domainFaultRank : DomainFault → Nat
  | .none => 0
  | _ => 1

/-- Duplicating receipts inside one provider does not create two-domain
connectivity: one provider compromise removes both separators. -/
theorem same_domain_duplicates_not_connectivity_two :
    ¬ TrustDomainConnectivityAtLeast
      observe selectedAB claim domain
      compromisedDomain domainFaultRank 2 := by
  intro connected
  have verified := connected .compromiseX (by simp [domainFaultRank])
  have sameEvidence :
      ChannelsAgree observe
        (SurvivingChannels selectedAB
          (CompromisedByDomain domain compromisedDomain)
          .compromiseX)
        .honest .attack := by
    intro evidenceChannel surviving
    cases evidenceChannel <;>
      simp [SurvivingChannels, selectedAB, CompromisedByDomain,
        domain, compromisedDomain] at surviving
  have equivalent := verified .honest .attack sameEvidence
  exact equivalent.mp True.intro

/-- Receipts placed in two independent trust domains tolerate compromise of
either one domain. -/
theorem independent_domains_connectivity_two :
    TrustDomainConnectivityAtLeast
      observe selectedAC claim domain
      compromisedDomain domainFaultRank 2 := by
  intro fault _below
  cases fault with
  | none =>
      exact verifies_with_surviving_receipt
        selectedAC
        (CompromisedByDomain domain compromisedDomain)
        .none .receiptA
        (by simp [selectedAC])
        (by simp [CompromisedByDomain, domain, compromisedDomain])
  | compromiseX =>
      exact verifies_with_surviving_receipt
        selectedAC
        (CompromisedByDomain domain compromisedDomain)
        .compromiseX .receiptC
        (by simp [selectedAC])
        (by simp [CompromisedByDomain, domain, compromisedDomain])
  | compromiseY =>
      exact verifies_with_surviving_receipt
        selectedAC
        (CompromisedByDomain domain compromisedDomain)
        .compromiseY .receiptA
        (by simp [selectedAC])
        (by simp [CompromisedByDomain, domain, compromisedDomain])

end LeanFinance.Epistemic.ConnectivityExample
