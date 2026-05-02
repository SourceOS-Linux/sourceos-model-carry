#!/usr/bin/env python3
"""Validate SourceOS LocalModelProfile examples.

This lightweight validator is intentionally stdlib-only so the carry-layer
contracts remain easy to run on developer workstations and CI bootstrap images.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/local-model-profile.schema.json"
EXAMPLES = sorted((ROOT / "examples").glob("local-model-profile.*.json"))


class ValidationError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_profile(path: Path, profile: dict[str, Any]) -> None:
    require(profile.get("schemaVersion") == "v0.1", f"{path}: schemaVersion must be v0.1")
    require(profile.get("kind") == "LocalModelProfile", f"{path}: kind must be LocalModelProfile")
    require(str(profile.get("profileId", "")).startswith("urn:srcos:model-profile:"), f"{path}: profileId must be a SourceOS model-profile URN")

    runtime = profile.get("runtime", {})
    require(runtime.get("kind") in {"ollama", "llama.cpp", "mlx", "openai-compatible", "other"}, f"{path}: unsupported runtime.kind")

    model = profile.get("model", {})
    require(model.get("name"), f"{path}: model.name is required")
    require(model.get("parameterClass") in {"sub-1b", "1b", "3b", "4b", "8b", "other"}, f"{path}: invalid parameterClass")
    require(model.get("licenseRef"), f"{path}: licenseRef is required")

    roles = profile.get("roles", [])
    require(isinstance(roles, list) and roles, f"{path}: roles must be a non-empty list")

    policy = profile.get("policy", {})
    require(policy.get("localOnlyDefault") is True, f"{path}: localOnlyDefault must default true")
    require(policy.get("sendPromptOffDeviceDefault") is False, f"{path}: prompts must not leave device by default")
    require(policy.get("allowToolUse") is False, f"{path}: local model profiles must not grant tool use by default")
    require(policy.get("allowNetwork") is False, f"{path}: local model profiles must not grant network by default")
    require(policy.get("requiresExplicitPull") is True, f"{path}: model pull/install must be explicit")


def main() -> int:
    load_json(SCHEMA)
    if not EXAMPLES:
        print("ERR: no local model profile examples found", file=sys.stderr)
        return 2

    try:
        for example in EXAMPLES:
            profile = load_json(example)
            validate_profile(example.relative_to(ROOT), profile)
            print(f"ok: {example.relative_to(ROOT)}")
    except ValidationError as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 1

    print("Local model profile validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
