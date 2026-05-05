#!/usr/bin/env python3
"""Validate SourceOSModelCarryRef projection examples.

This validator is intentionally lightweight and stdlib-only. Full JSON Schema
validation belongs in SourceOS-Linux/sourceos-spec; this repository validates the
carry-layer invariants it must preserve locally.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples").glob("sourceos-model-carry-ref.*.json"))


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


def validate_ref(path: Path, ref: dict[str, Any]) -> None:
    rel = path.relative_to(ROOT)
    require(ref.get("type") == "SourceOSModelCarryRef", f"{rel}: type must be SourceOSModelCarryRef")
    require(str(ref.get("id", "")).startswith("urn:srcos:model-carry-ref:"), f"{rel}: id must be a model-carry-ref URN")
    require(ref.get("specVersion") == "2.1.0", f"{rel}: specVersion must be 2.1.0")
    require(ref.get("modelRef"), f"{rel}: modelRef is required")
    require(ref.get("governanceRef"), f"{rel}: governanceRef is required")
    require(str(ref.get("routerProfileRef", "")).startswith("urn:srcos:model-router-profile:"), f"{rel}: routerProfileRef must be a model-router-profile URN")
    require(ref.get("carryPolicy") in {"reference-only", "download-on-demand", "preload-reference", "disabled"}, f"{rel}: invalid carryPolicy")
    require(ref.get("cachePolicy") in {"none", "metadata-only", "weights-cache-allowed", "kv-cache-allowed", "embedding-cache-allowed"}, f"{rel}: invalid cachePolicy")
    require(ref.get("mutableModelState") is False, f"{rel}: mutableModelState must be false")
    for release_ref in ref.get("releaseSetRefs", []):
        require(str(release_ref).startswith("urn:srcos:release-set:"), f"{rel}: releaseSetRefs entries must be release-set URNs")
    for fallback_ref in ref.get("fallbackRefs", []):
        require(str(fallback_ref).startswith("urn:srcos:model-carry-ref:"), f"{rel}: fallbackRefs entries must be model-carry-ref URNs")


def main() -> int:
    if not EXAMPLES:
        print("ERR: no SourceOSModelCarryRef examples found", file=sys.stderr)
        return 2
    try:
        for example in EXAMPLES:
            validate_ref(example, load_json(example))
            print(f"ok: {example.relative_to(ROOT)}")
    except ValidationError as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 1
    print("SourceOSModelCarryRef validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
