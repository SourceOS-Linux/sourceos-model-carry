#!/usr/bin/env python3
"""Validate SourceOS ModelCarryAuthorizationBoundary examples."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts" / "model-carry-authorization-boundary.schema.json"
VALID = ROOT / "examples" / "model-carry-authorization-boundary.local-llama32-1b.json"
INVALID_PROMPT_EGRESS = ROOT / "examples" / "model-carry-authorization-boundary.prompt-egress.invalid.json"
INVALID_DOWNLOAD = ROOT / "examples" / "model-carry-authorization-boundary.download.invalid.json"

FORBIDDEN_AUTHORIZATIONS = (
    "authorizesPromptEgress",
    "authorizesNetworkAccess",
    "authorizesToolUse",
    "authorizesModelDownload",
    "authorizesTrainingOnUserData",
    "authorizesModelPromotion",
    "authorizesLifecycleMutation",
)


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError(f"{path.relative_to(ROOT)}: expected JSON object")
    return payload


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_schema(schema: dict[str, Any]) -> None:
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema draft mismatch")
    require(schema.get("type") == "object", "schema must describe object")
    require(schema.get("additionalProperties") is False, "schema must be closed")


def validate_boundary(path: Path, record: dict[str, Any]) -> None:
    require(record.get("schemaVersion") == "v0.1", f"{path}: schemaVersion must be v0.1")
    require(record.get("kind") == "ModelCarryAuthorizationBoundary", f"{path}: kind mismatch")
    require(str(record.get("boundaryId", "")).startswith("urn:srcos:model-carry-boundary:"), f"{path}: boundaryId must be SourceOS boundary URN")
    require(str(record.get("profileRef", "")).startswith("urn:srcos:model-profile:"), f"{path}: profileRef must point at model profile")
    require(record.get("profileKind") == "LocalModelProfile", f"{path}: profileKind must be LocalModelProfile")

    carry_scope = record.get("carryScope", {})
    require(carry_scope.get("mayCarryProfile") is True, f"{path}: mayCarryProfile must be true")
    require(carry_scope.get("mayCarryServiceRef") is True, f"{path}: mayCarryServiceRef must be true")
    require(carry_scope.get("mayEmitEvidence") is True, f"{path}: mayEmitEvidence must be true")

    auth = record.get("authorizationBoundary", {})
    for field in FORBIDDEN_AUTHORIZATIONS:
        require(auth.get(field) is False, f"{path}: carry profile must not set {field}=true")

    evidence_refs = record.get("evidenceRefs", [])
    require(isinstance(evidence_refs, list) and evidence_refs, f"{path}: evidenceRefs required")
    for ref in evidence_refs:
        require(isinstance(ref, str) and ref.startswith("evidence://"), f"{path}: evidenceRefs must use evidence:// refs")


def expect_invalid(path: Path) -> None:
    try:
        validate_boundary(path.relative_to(ROOT), load_json(path))
    except ValidationError:
        return
    raise ValidationError(f"invalid fixture unexpectedly validated: {path.relative_to(ROOT)}")


def main() -> int:
    try:
        validate_schema(load_json(SCHEMA))
        validate_boundary(VALID.relative_to(ROOT), load_json(VALID))
        expect_invalid(INVALID_PROMPT_EGRESS)
        expect_invalid(INVALID_DOWNLOAD)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"ERR: {exc}")
        return 1
    print("Model carry authorization boundary validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
