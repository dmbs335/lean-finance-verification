# Proof-Carrying Execution State Machine

This layer formalizes the boundary between an accepted policy action and a reconciled portfolio state.

```text
proposed
→ shielded
→ authorized
→ submitted
→ acknowledged
→ partiallyFilled
→ filled | cancelled | expired
→ reconciled
```

Every transition is checked against a finite lifecycle relation. Submission requires `microAutonomy` or `boundedAutonomy`, a positive authorized quantity, and a quantity no larger than the registered capital cap. `recommend`, `shadow`, `fallback`, and `revoked` cannot submit.

## Fill invariants

A proof-carrying execution certificate checks:

- fill identifiers are unique;
- fills occur only after broker acknowledgement;
- cumulative fill quantity never exceeds authorization;
- a `filled` terminal state has exactly the authorized quantity;
- buy prices do not exceed the limit and sell prices do not fall below it;
- cash and inventory are reconciled from the exact fill ledger.

The controlled buy authorizes 100 units at limit 10 and receives fills of 40 and 60 units with one unit of fee each. The exact result is:

```text
filled quantity   100
cash delta       -1002
inventory delta   100
final cash        8998
final inventory   100
```

Counterfactual tests reject revoked authority, overfill, duplicate fill identifiers, illegal lifecycle transitions, and limit-price violations.

## Assurance boundary

The broker acknowledgement and fill records are declared controlled inputs. This module does not authenticate a broker connection, prove exchange finality, calibrate market impact, or grant Monun order authority. It defines the certificate that a later runtime adapter and independent receipt provider must satisfy.
