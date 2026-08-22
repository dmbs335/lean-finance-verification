# Signed Point-in-Time Vendor Package Import

A production point-in-time study must preserve the provider's actual publication timestamps, revision identities, listing history, corporate actions, license identifier, and redistribution policy. This importer verifies that boundary before translating provider CSV files into the normalized `lfv-pit-micro-study-v1` contract.

The package contains exactly one file for vintages, listings, prices, and corporate actions. The signed manifest binds each relative path, schema, row count, SHA-256 digest, vendor/package/license identity, redistribution policy, signing time, and verifier-selected public key. Unsafe paths, missing kinds, duplicate kinds, altered files, schema drift, row-count drift, and signature substitution are rejected.

The import then checks revision monotonicity and asset/vintage references. The resulting study is passed through the existing exact universe, availability, corporate-action, and evaluation-contract checker.

The checked-in package is synthetic and metadata-only. It demonstrates the import and verification pipeline without pretending to redistribute licensed market data. Replacing it with a real provider package requires lawful access and preservation of the provider's original manifest semantics; reconstructing historical publication metadata from a present-day download is not equivalent.
