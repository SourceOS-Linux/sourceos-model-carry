#!/usr/bin/env python3
"""Validate SourceOS ModelCarryManifest examples.

Enforces the content-addressed carry invariants that the model-router relies on:

  1. SHA-256 is the authoritative content-hash algorithm (FIPS 180-4).
  2. Every entry carries a non-null content hash and policy hash.
  3. Integrity failure is a hard stop, and transport must be integrity-checked.
  4. The manifest is hash-chained: only the genesis manifest (version 1) may omit
     the previous-manifest link.
  5. Every adapter is bound to a base entry that exists in the manifest, and the
     adapter's pinned base content hash matches that base. This eliminates silent
     adapter/base drift by construction.

Boundary: this checker is structural. It does not fetch artifacts, verify real
cryptographic content, or authorize runtime execution.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts" / "model-carry-manifest.schema.json"
VALID = ROOT / "examples" / "model-carry-manifest.laptop-safe.json"
INVALID_DRIFT = ROOT / "examples" / "model-carry-manifest.adapter-base-drift.invalid.json"
INVALID_MISSING_BASE = ROOT / "examples" / "model-carry-manifest.adapter-missing-base.invalid.json"
INVALID_SOFT_INTEGRITY = ROOT / "examples" / "model-carry-manifest.integrity-not-hardstop.invalid.json"

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


def validate_manifest(name: str, record: dict[str, Any]) -> None:
    require(record.get("schemaVersion") == "v0.1", f"{name}: schemaVersion must be v0.1")
    require(record.get("kind") == "ModelCarryManifest", f"{name}: kind must be ModelCarryManifest")
    require(str(record.get("manifestId", "")).startswith("urn:srcos:model-carry-manifest:"),
            f"{name}: manifestId must be a SourceOS model-carry-manifest URN")

    version = record.get("version")
    require(isinstance(version, int) and version >= 1, f"{name}: version must be an integer >= 1")

    prev = record.get("prevManifestSha256", "missing")
    require(prev != "missing", f"{name}: prevManifestSha256 must be present (null only for the genesis manifest)")
    if version == 1:
        require(prev is None, f"{name}: genesis manifest (version 1) must have null prevManifestSha256")
    else:
        require(is_sha256(prev), f"{name}: non-genesis manifest must link previous manifest by SHA-256 (hash chain)")

    integrity = record.get("integrity", {})
    require(integrity.get("contentHashAlgorithm") == "sha256",
            f"{name}: contentHashAlgorithm must be sha256 (FIPS 180-4 authoritative)")
    require(integrity.get("transportMustBeIntegrityChecked") is True,
            f"{name}: transportMustBeIntegrityChecked must be true")
    require(integrity.get("integrityFailureIsHardStop") is True,
            f"{name}: integrityFailureIsHardStop must be true (integrity failure is a hard stop, not a fallback)")

    entries = record.get("entries", [])
    require(isinstance(entries, list) and entries, f"{name}: entries must be a non-empty array")

    by_id: dict[str, dict[str, Any]] = {}
    for entry in entries:
        entry_id = entry.get("entryId", "")
        require(str(entry_id).startswith("urn:srcos:model-carry-entry:"),
                f"{name}: entryId must be a SourceOS model-carry-entry URN")
        require(entry_id not in by_id, f"{name}: duplicate entryId {entry_id}")
        require(is_sha256(entry.get("contentSha256")), f"{name}: {entry_id} contentSha256 must be a SHA-256 digest")
        require(is_sha256(entry.get("policySha256")), f"{name}: {entry_id} policySha256 must be a SHA-256 digest")
        targeting = entry.get("targeting", {})
        require(isinstance(targeting, dict) and targeting.get("deviceClass"),
                f"{name}: {entry_id} must carry a targeting predicate with deviceClass")
        by_id[entry_id] = entry

    for entry in entries:
        entry_id = entry.get("entryId", "")
        kind = entry.get("entryKind")
        require(kind in ("base", "adapter"), f"{name}: {entry_id} entryKind must be base or adapter")
        if kind == "base":
            require(entry.get("baseEntryRef") is None and entry.get("baseContentSha256") is None,
                    f"{name}: {entry_id} base entry must not set baseEntryRef/baseContentSha256")
            continue
        # adapter: enforce base-version binding
        base_ref = entry.get("baseEntryRef")
        require(base_ref in by_id, f"{name}: {entry_id} adapter references unknown base {base_ref}")
        base = by_id[base_ref]
        require(base.get("entryKind") == "base", f"{name}: {entry_id} adapter must bind to a base entry, not {base_ref}")
        require(is_sha256(entry.get("baseContentSha256")),
                f"{name}: {entry_id} adapter must pin baseContentSha256")
        require(entry.get("baseContentSha256") == base.get("contentSha256"),
                f"{name}: {entry_id} adapter/base drift: pinned baseContentSha256 does not match base contentSha256")


def expect_invalid(path: Path) -> None:
    try:
        validate_manifest(path.name, load_json(path))
    except ValidationError:
        return
    raise ValidationError(f"invalid fixture unexpectedly validated: {path.name}")


def main() -> int:
    try:
        validate_schema(load_json(SCHEMA))
        validate_manifest(VALID.name, load_json(VALID))
        expect_invalid(INVALID_DRIFT)
        expect_invalid(INVALID_MISSING_BASE)
        expect_invalid(INVALID_SOFT_INTEGRITY)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"ERR: {exc}")
        return 1
    print("Model carry manifest validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
