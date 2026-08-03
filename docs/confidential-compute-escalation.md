# Confidential Compute Escalation

The confidential-compute escalation contract governs how model execution escalates
to a higher confidential-compute tier based on the data-residency / sensitivity
class of the inputs. It is the SourceOS analogue of Apple's on-device to Private
Cloud Compute boundary (SourceOS-vs-Apple ModelCarry spec, section 5.2): where does
an over-scale or high-sensitivity request go, and under what attested-compute
guarantee?

- Contract: `contracts/confidential-compute-escalation.schema.json`
- Validator: `tools/validate_confidential_compute_escalations.py` (`make validate-confidential-compute-escalation`)
- Example: `examples/confidential-compute-escalation.attested-tee.json`

## The tier lattice

`computeTiers` is an ordered, totally ordered lattice of confidential-compute
postures, weakest first:

| tierClass | Guarantee | Attestation |
|---|---|---|
| `on_device` | Execution stays on the workstation. | none |
| `sealed_enclave` | Execution in a sealed enclave. | `enclave_measurement` |
| `attested_tee` | Execution in a remotely attested TEE. | `tee_remote_attestation` |

Each request carries a sensitivity class (`public` / `internal` / `confidential` /
`restricted`) and a `dataResidencyClass` aligned with the estate InferenceReceipt
residency vocabulary (`on_device_only` / `sealed_compute_only` /
`attested_compute_only`). `sensitivityClassMap` binds each class to the weakest
tier permitted to process it. The `decision` records the tier actually chosen, the
reason, the attestation reference, and a SHA-256 receipt -- escalation is a
first-class, receipted provenance record, not an implicit routing side effect.

## Invariants (enforced by the validator)

| Invariant | Rule |
|---|---|
| Fail-closed | A request whose class requires a minimum tier and is run **below** that tier is **rejected**, never silently downgraded. This is the core invariant. |
| Attestation required | A chosen tier with `requiresAttestation: true` MUST carry a non-null `attestationRef`; a missing attestation is a hard stop. |
| Totally ordered lattice | `computeTiers` ranks are strictly increasing in array order; a non-monotonic ordering is rejected. |
| Declared class | The request's sensitivity class MUST appear in `sensitivityClassMap`; an unknown class is rejected, never defaulted to the weakest tier. |
| Authoritative receipt hash | `invariants.receiptHashAlgorithm` is `sha256` (FIPS 180-4); `decision.receiptSha256` is a SHA-256 digest. |

## Teeth (negative fixtures)

| Fixture | Rejected because |
|---|---|
| `confidential-compute-escalation.below-minimum-tier.invalid.json` | A `restricted`-class request (minimum: attested TEE, rank 2) was run on-device (rank 0). Fail-closed. |
| `confidential-compute-escalation.missing-attestation.invalid.json` | The chosen attested TEE tier requires attestation, but the decision has no `attestationRef`. |
| `confidential-compute-escalation.non-monotonic-tiers.invalid.json` | The tier lattice is not strictly monotonic by rank. |
| `confidential-compute-escalation.unknown-class.invalid.json` | The request's class is not declared in `sensitivityClassMap`. |

## Carry boundary

This contract is a decision/verification object. It does not perform live TEE
attestation, verify real enclave measurements, provision compute, or authorize
runtime execution. It proves that an escalation decision is well formed and
fail-closed before it is acted on.

## Not yet in scope (tracked as follow-up)

- Live TEE attestation verification (real enclave measurement / remote-attestation
  quote validation) rather than a structural attestation reference.
- Governed staged pre-load plus atomic swap under a resource governor
  (`sourceos-model-carry#21`).
