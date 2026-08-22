# Experimental Zero-Knowledge Zero-Count Receipts

This backend replaces selective count openings with Pedersen commitments and Fiat–Shamir Schnorr proofs that a forbidden action's commitment has an opening with count zero. The proof reveals neither the count nor the blinding scalar. Each disclosed commitment is still tied to the signed complete-histogram root by a Merkle inclusion path.

## Construction

For a q-order subgroup of a safe-prime field, the runner commits to each action count m as:

```text
C = g^m h^r mod p
```

To prove m = 0, the runner proves knowledge of r such that `C = h^r` using a Schnorr proof whose Fiat–Shamir challenge binds the policy digest, parameter digest, histogram root, action ID, commitment, and announcement. A nonzero count does not provide that opening unless the prover knows the discrete-log relation between the independently derived generators.

## Security boundary

This implementation is an experimental interoperability and formal-contract prototype, not an audited production ZK system. Its custom 256-bit safe-prime parameters, hash-to-generator procedure, transcript encoding, side-channel behavior, and random-oracle assumptions require independent cryptographic review. Production deployment should replace this backend with an audited proof system and standardized group while preserving the normalized Lean `PrivateAbsenceCertificate` interface.

The runner still attests that the signed commitment root represents the complete execution histogram. The ZK proof hides forbidden counts and proves they are zero relative to those commitments; it does not by itself force a malicious runner to include every real execution event.
