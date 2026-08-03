#!/usr/bin/env python3
"""Validate SourceOS ConfidentialComputeEscalation examples.

Enforces the tiered confidential-compute escalation invariants (SourceOS-vs-Apple
ModelCarry spec, section 5.2) that the model-router relies on:

  1. SHA-256 is the authoritative receipt-hash algorithm (FIPS 180-4).
  2. The compute-tier lattice is totally ordered: ranks are strictly increasing in
     array order. A non-monotonic ordering makes a minimum-tier comparison
     meaningless and is rejected.
  3. Fail-closed (core invariant): a request whose sensitivity class requires a
     minimum tier MUST run at or above that tier. A decision that runs below the
     required minimum is rejected, never silently downgraded.
  4. A chosen tier that requiresAttestation MUST carry a non-null attestationRef;
     a missing attestation is a hard stop.
  5. The request's sensitivity class MUST be declared in sensitivityClassMap; an
     unknown class is rejected rather than defaulted to the weakest tier.

Boundary: this checker is structural. It does not perform live TEE attestation,
verify real enclave measurements, or authorize runtime execution. Live attestation
and governed staged pre-load are tracked as follow-up issues.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts" / "confidential-compute-escalation.schema.json"
VALID = ROOT / "examples" / "confidential-compute-escalation.attested-tee.json"
INVALID_BELOW_MIN = ROOT / "examples" / "confidential-compute-escalation.below-minimum-tier.invalid.json"
INVALID_NO_ATTEST = ROOT / "examples" / "confidential-compute-escalation.missing-attestation.invalid.json"
INVALID_NON_MONOTONIC = ROOT / "examples" / "confidential-compute-escalation.non-monotonic-tiers.invalid.json"
INVALID_UNKNOWN_CLASS = ROOT / "examples" / "confidential-compute-escalation.unknown-class.invalid.json"

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError(f"{path.name}: expected JSON object")
    return payload


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.match(value))


def validate_schema(schema: dict[str, Any]) -> None:
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema draft mismatch")
    require(schema.get("type") == "object", "schema must describe object")
    require(schema.get("additionalProperties") is False, "schema must be closed")


def validate_escalation(name: str, record: dict[str, Any]) -> None:
    require(record.get("schemaVersion") == "v0.1", f"{name}: schemaVersion must be v0.1")
    require(record.get("kind") == "ConfidentialComputeEscalation", f"{name}: kind must be ConfidentialComputeEscalation")
    require(str(record.get("escalationId", "")).startswith("urn:srcos:cc-escalation:"),
            f"{name}: escalationId must be a SourceOS cc-escalation URN")

    inv = record.get("invariants", {})
    require(inv.get("belowMinimumTierIsRejected") is True,
            f"{name}: belowMinimumTierIsRejected must be true (fail-closed core invariant)")
    require(inv.get("unattestedTierRequiringAttestationIsRejected") is True,
            f"{name}: unattestedTierRequiringAttestationIsRejected must be true")
    require(inv.get("tierOrderingMustBeMonotonic") is True,
            f"{name}: tierOrderingMustBeMonotonic must be true")
    require(inv.get("receiptHashAlgorithm") == "sha256",
            f"{name}: receiptHashAlgorithm must be sha256 (FIPS 180-4 authoritative)")

    # --- Compute-tier lattice: totally ordered, strictly increasing rank ---
    tiers = record.get("computeTiers", [])
    require(isinstance(tiers, list) and len(tiers) >= 2, f"{name}: computeTiers must be an array of at least 2 tiers")

    by_ref: dict[str, dict[str, Any]] = {}
    prev_rank: int | None = None
    for tier in tiers:
        tier_ref = tier.get("tierRef", "")
        require(str(tier_ref).startswith("urn:srcos:cc-tier:"), f"{name}: tierRef must be a SourceOS cc-tier URN")
        require(tier_ref not in by_ref, f"{name}: duplicate tierRef {tier_ref}")
        rank = tier.get("rank")
        require(isinstance(rank, int) and rank >= 0, f"{name}: {tier_ref} rank must be an integer >= 0")
        # Strict monotonicity in array order: the tier lattice must be totally ordered.
        require(prev_rank is None or rank > prev_rank,
                f"{name}: computeTiers not strictly monotonic by rank at {tier_ref} "
                f"(rank {rank} does not exceed previous {prev_rank})")
        prev_rank = rank
        require(isinstance(tier.get("requiresAttestation"), bool),
                f"{name}: {tier_ref} requiresAttestation must be a boolean")
        by_ref[tier_ref] = tier

    # --- Sensitivity/residency class -> minimum-tier map references real tiers ---
    class_map = record.get("sensitivityClassMap", [])
    require(isinstance(class_map, list) and class_map, f"{name}: sensitivityClassMap must be a non-empty array")
    min_tier_by_class: dict[str, str] = {}
    for m in class_map:
        cls = m.get("sensitivityClass")
        min_ref = m.get("minimumTierRef")
        require(min_ref in by_ref, f"{name}: sensitivityClassMap references unknown tier {min_ref}")
        require(cls not in min_tier_by_class, f"{name}: duplicate sensitivityClass {cls} in map")
        min_tier_by_class[cls] = min_ref

    # --- The governed, receipted decision ---
    decision = record.get("decision", {})
    req_class = decision.get("requestSensitivityClass")
    chosen_ref = decision.get("chosenTierRef")

    # Unknown class is rejected, not defaulted (fail-closed).
    require(req_class in min_tier_by_class,
            f"{name}: requestSensitivityClass {req_class} not declared in sensitivityClassMap (fail-closed)")
    require(chosen_ref in by_ref, f"{name}: decision chosenTierRef references unknown tier {chosen_ref}")
    require(is_sha256(decision.get("receiptSha256")), f"{name}: decision receiptSha256 must be a SHA-256 digest")

    chosen = by_ref[chosen_ref]
    required_min = by_ref[min_tier_by_class[req_class]]

    # Core invariant: fail-closed. Chosen tier must be at or above the required minimum.
    require(chosen["rank"] >= required_min["rank"],
            f"{name}: below-minimum tier: class {req_class} requires tier rank >= {required_min['rank']} "
            f"({required_min['tierRef']}) but ran at rank {chosen['rank']} ({chosen_ref}) -- REJECTED (fail-closed)")

    # A chosen tier that requires attestation must carry an attestation reference.
    if chosen.get("requiresAttestation"):
        att = decision.get("attestationRef")
        require(isinstance(att, str) and att.strip() != "",
                f"{name}: chosen tier {chosen_ref} requiresAttestation but decision has no attestationRef -- REJECTED")


def expect_invalid(path: Path) -> None:
    try:
        validate_escalation(path.name, load_json(path))
    except ValidationError:
        return
    raise ValidationError(f"invalid fixture unexpectedly validated: {path.name}")


def main() -> int:
    try:
        validate_schema(load_json(SCHEMA))
        validate_escalation(VALID.name, load_json(VALID))
        expect_invalid(INVALID_BELOW_MIN)
        expect_invalid(INVALID_NO_ATTEST)
        expect_invalid(INVALID_NON_MONOTONIC)
        expect_invalid(INVALID_UNKNOWN_CLASS)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"ERR: {exc}")
        return 1
    print("Confidential compute escalation validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
