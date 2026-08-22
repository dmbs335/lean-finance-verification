# Multi-Provider External Evidence

The RFC 3161 adapter verifies one signed timestamp against verifier-selected CA trust. This layer adds a second provider type: an append-only Merkle transparency receipt with a verifier-selected public key, signed tree head, and inclusion proof. A normalized quorum then requires every receipt to bind the same target, precede the decision cutoff, use a unique provider ID, and span a configured number of distinct trust domains.

## Signed transparency receipt

A receipt contains:

- a SHA-256 target digest as one domain-separated Merkle leaf;
- a power-of-two tree size, leaf index, and ordered inclusion path;
- a signed tree head containing provider ID, root, tree size, and anchor time;
- a SHA-256 binding to the verifier-selected public key;
- an explicit provider ID and trust-domain ID.

The reference implementation signs tree heads with RSA/SHA-256 through OpenSSL. Production deployments may replace the signing primitive while preserving the normalized receipt contract.

## Quorum semantics

Two receipts from the same operator do not satisfy a two-domain policy. Provider aliases also cannot be repeated because provider IDs must be unique. The Lean `ProviderQuorumCertificate` states the provider-independent contract after cryptographic verification.

RFC 3161 evidence can be normalized into the same structure after the existing adapter verifies its nonce, imprint, signature, certificate chain, generation time, and trust bundle. A high-assurance policy can therefore combine one TSA, one independent transparency log, and one remote execution provider without treating them as interchangeable trust roots.

The tests generate independent RSA keys, construct Merkle trees, sign tree heads, and reject path tampering, signature tampering, verifier-key substitution, same-domain duplication, target mismatch, and late evidence.
