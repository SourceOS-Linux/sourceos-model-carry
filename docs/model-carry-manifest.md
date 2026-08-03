# Model Carry Manifest

The model carry manifest is the content-addressed, hash-chained catalog the
SourceOS model-router carries. It names every base model and adapter with a
verifiable identity, a targeting predicate, and the policy bound to it. It is the
model-layer analogue of Exodus provenance: model identity is verifiable, not
asserted.

- Contract: `contracts/model-carry-manifest.schema.json`
- Validator: `tools/validate_model_carry_manifests.py` (`make validate-model-carry-manifest`)
- Example: `examples/model-carry-manifest.laptop-safe.json`

## Why

This closes three gaps identified in the SourceOS-vs-Apple model-carry analysis,
where Apple's delivery discipline exposed missing primitives in our carry path:

1. **No content-addressed model manifest.** The router routed, but nothing named
   every model+adapter with its targeting predicate and integrity hash. Without
   it, provenance at the model layer was asserted, not verifiable.
2. **Adapter/base version binding was not enforced.** A base update did not
   mechanically force adapter re-delivery, inviting silent drift between an
   adapter and the base it was trained against.
3. **Encrypted, integrity-checked transport was not an invariant.** Integrity was
   optional rather than a hard stop.

## Invariants (enforced by the validator)

| Invariant | Rule |
|---|---|
| Authoritative hash | `integrity.contentHashAlgorithm` is `sha256` (FIPS 180-4). |
| Content-addressed | Every entry carries a non-null `contentSha256` and `policySha256`. |
| Integrity is a hard stop | `integrityFailureIsHardStop` and `transportMustBeIntegrityChecked` are `true`. |
| Hash chain | `version` 1 has null `prevManifestSha256`; every later version links the previous manifest by SHA-256. |
| Adapter/base binding | Every adapter references an existing base entry and pins a `baseContentSha256` that equals that base's `contentSha256`. Drift is rejected by construction. |
| Base entries | A base entry sets `baseEntryRef` and `baseContentSha256` to null. |
| Targeting predicate | Every entry carries a `targeting` predicate with at least a `deviceClass`. |

## Carry boundary

The manifest is a reference/verification object. It does not authorize runtime
execution, prompt egress, tool use, model download, training, or promotion. Those
remain outside the mutable workstation image, consistent with the carry-only
doctrine in `repo.maturity.yaml`.

## Not yet in scope (tracked as issues)

- Governed staged pre-load plus atomic swap under a disk/CPU resource governor.
- Tiered escalation contract: local-by-default to an attested confidential-compute
  target, with the escalation decision and its confidence propagated as a
  first-class provenance record.
