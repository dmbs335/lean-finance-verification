# Epistemic Connectivity

Ordinary Evidence Separation asks whether every history pair with different claim truth values is distinguished by at least one selected channel. That criterion is brittle: a single compromised receipt or provider can erase the only separator.

**Epistemic Connectivity** measures how many independent evidence failures a verification claim can survive.

## Abstract fault model

`RobustlyVerifies` is parameterized by:

```text
Fault
allowed  : Fault → Prop
survives : Fault → Channel → Prop
```

This abstraction can represent:

- loss of individual evidence channels;
- compromise of a timestamp or executor provider;
- correlated failure of all channels in one cloud account;
- certificate-authority compromise;
- another explicitly modeled fault domain.

For every allowed fault, the surviving selected channels must still verify the claim.

## Robust cut-set duality

The central theorem is:

```lean
RobustlyVerifies channel selected claim allowed survives
↔
RobustlyHitsEveryClaimDisagreement
  channel selected claim allowed survives
```

Thus robust verification does not require a new semantic theory. It is the original separator condition quantified over every admissible failure scenario:

> Every claim-disagreement pair must retain at least one live selected separator after every allowed fault.

## Channel connectivity

`ChannelConnectivityAtLeast level` permits every duplicate-free channel-failure list whose length is smaller than `level`.

```text
level 0  vacuous lower bound
level 1  ordinary verification
level 2  survives any one channel failure
level 3  survives any two channel failures
```

The repository proves that higher connectivity implies every lower level and that connectivity one implies ordinary verification.

## Trust-domain connectivity

Raw channel count can overstate resilience. Two timestamp tokens signed by the same provider, or two logs controlled by one cloud account, may fail together.

`TrustDomainConnectivityAtLeast` maps each channel to a domain:

```text
domain : Channel → TrustDomain
```

A failed domain disables every channel mapped to it. Consequently, duplicating evidence inside one provider cannot increase trust-domain connectivity. Resilience requires separators in genuinely independent domains.

## Design implication

Multi-anchor policies should be derived from this theory rather than hard-coded as “two signatures are better than one.” The relevant question is:

```text
For every claim-disagreement pair,
how many independent trust domains contain a selected separator?
```

A timestamp provider may be essential for a preregistration-time claim yet irrelevant to hidden execution. A remote executor may separate execution histories but share an administrative domain with the CI system. Robust portfolio synthesis must account for those semantics and correlations simultaneously.

## Next executable layer

The next synthesis backend will enumerate bounded fault scenarios and optimize:

```text
minimum cost
subject to trust-domain connectivity ≥ required level
```

It will emit both the selected portfolio and concrete history/fault counterexamples for every cheaper non-robust candidate, preserving the existing proof-carrying optimizer boundary.
