# Point-in-Time Data, Universe, and Corporate-Action Contracts

`PointInTimeData.lean` separates logical datasets from immutable publication vintages, requires retrieval by the decision cutoff, derives exact universes from listing and delisting records, and binds adjusted series to corporate actions announced before generation.

The Python micro-study exercises the complete validation path on a deterministic three-asset fixture. `BETA` is selected before its later delisting and excluded exactly at the delisting timestamp. `GAMMA` is in the universe before it has enough history to receive a score, demonstrating that universe membership and signal availability are different contracts.

The checker rejects:

- a later dataset revision used at an earlier decision;
- a survivors-only universe that deletes `BETA` from historical membership;
- a delisted asset retained at or after its delisting timestamp;
- a corporate action announced after an adjusted series was generated;
- an evaluation contract registered after the first decision.

The included values are a controlled micro-study, not a claim about real asset performance. It establishes the proof-carrying data interface needed for a subsequent study backed by a public or licensed point-in-time vendor. Such a production study must preserve the vendor's publication timestamps, revision identifiers, listing history, and redistribution terms rather than replacing them with reconstructed present-day data.
