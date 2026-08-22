# Selective-Disclosure Execution Receipts

A full executor log can verify search and data-access integrity but may reveal strategy internals, parameter exploration, and proprietary workflow structure. This layer commits to a complete histogram over a fixed finite action universe and selectively opens only policy-forbidden classes.

Each action-count leaf is salted and committed under a Merkle root. The runner signs the root, policy digest, action-universe digest, total event count, completion time, runner identity, and trust domain. The verifier requires one zero-valued inclusion proof for every forbidden action class and rejects additional or missing disclosures.

The disclosed receipt reveals:

- the fixed action universe and policy identity;
- the total number of events, because the runner signs it;
- which classes are forbidden;
- that each forbidden class has committed count zero.

It does not reveal the allowed action counts or event sequence. Completeness of the histogram remains an attestation by the independently trusted runner; a dishonest runner can sign a false histogram. The Lean certificate makes this boundary explicit through `disclosureSound`.

This construction is selective disclosure, not a zero-knowledge proof. A future ZK backend can replace the opened count leaves with proofs that the committed counts are zero and that the total equals the committed histogram sum, while preserving the normalized `SelectiveAbsenceCertificate` contract.
