#!/usr/bin/env python3
"""Validate SourceOS Portable AI Kit carry-pack examples.

This validator is intentionally stdlib-only. It performs semantic checks for
portable model-carry examples before the contracts are promoted to sourceos-spec.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACK_SCHEMA = ROOT / "contracts/model-carry-pack.schema.json"
ROOT_SCHEMA = ROOT / "contracts/portable-ai-root.schema.json"
PACK_EXAMPLES = sorted((ROOT / "examples").glob("model-carry-pack.*.json"))
ROOT_EXAMPLES = sorted((ROOT / "examples").glob("portable-ai-root.*.json"))

PROFILE_MIN_FREE_GB = {
    "tiny-router": 8,
    "laptop-safe": 16,
    "office-local": 32,
    "code-local": 32,
    "field-kit": 64,
    "byom-gguf": 8,
}

ALLOWED_PROFILES = set(PROFILE_MIN_FREE_GB)
ALLOWED_SURFACES = {"turtleterm", "agent-term", "bearbrowser", "local-web", "anythingllm-adapter"}


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


def validate_pack(path: Path, pack: dict[str, Any]) -> None:
    rel = path.relative_to(ROOT)
    require(pack.get("schemaVersion") == "v0.1", f"{rel}: schemaVersion must be v0.1")
    require(pack.get("kind") == "ModelCarryPack", f"{rel}: kind must be ModelCarryPack")
    require(str(pack.get("packId", "")).startswith("urn:srcos:model-carry-pack:"), f"{rel}: packId must be a SourceOS model-carry-pack URN")

    profile = pack.get("profileKey")
    require(profile in ALLOWED_PROFILES, f"{rel}: unsupported profileKey")

    model = pack.get("model", {})
    require(model.get("name"), f"{rel}: model.name is required")
    require(model.get("format") in {"ollama-ref", "gguf", "runtime-managed", "openai-compatible-local", "other"}, f"{rel}: unsupported model.format")

    runtime = pack.get("runtimeCompatibility", [])
    require(isinstance(runtime, list) and runtime, f"{rel}: runtimeCompatibility must be non-empty")

    footprint = pack.get("footprint", {})
    require(footprint.get("minimumFreeGb", 0) >= PROFILE_MIN_FREE_GB[profile], f"{rel}: minimumFreeGb below profile floor")
    require(footprint.get("recommendedFreeGb", 0) >= footprint.get("minimumFreeGb", 0), f"{rel}: recommendedFreeGb must be >= minimumFreeGb")
    require(footprint.get("recommendedRamGb", 0) >= footprint.get("minimumRamGb", 0), f"{rel}: recommendedRamGb must be >= minimumRamGb")

    provenance = pack.get("provenance", {})
    require(provenance.get("licenseRef"), f"{rel}: licenseRef is required")
    sha = provenance.get("sha256")
    if sha is not None:
        require(isinstance(sha, str) and len(sha) == 64, f"{rel}: sha256 must be a 64-char hex string when present")

    policy = pack.get("policy", {})
    require(policy.get("localOnlyDefault") is True, f"{rel}: localOnlyDefault must be true")
    require(policy.get("promptEgressDefault") == "deny", f"{rel}: promptEgressDefault must be deny")
    require(policy.get("allowToolUseDefault") is False, f"{rel}: allowToolUseDefault must be false")
    require(policy.get("allowNetworkDefault") is False, f"{rel}: allowNetworkDefault must be false")
    require(policy.get("requiresExplicitImport") is True, f"{rel}: requiresExplicitImport must be true")
    require(policy.get("requiresEvidence") is True, f"{rel}: requiresEvidence must be true")

    if profile == "byom-gguf":
        require(provenance.get("sha256RequiredBeforeEligibility") is True, f"{rel}: BYOM must require hash before eligibility")
        require(policy.get("eligibleForRoutingBeforeHash") is False, f"{rel}: BYOM must not be route-eligible before hash")
        require("byom-unverified" in pack.get("labels", []), f"{rel}: BYOM placeholder must carry byom-unverified label")

    evidence = pack.get("evidence", {})
    require(evidence.get("emitPromptHashOnly") is True, f"{rel}: evidence must be prompt-hash-only")


def validate_root(path: Path, root: dict[str, Any]) -> None:
    rel = path.relative_to(ROOT)
    require(root.get("schemaVersion") == "v0.1", f"{rel}: schemaVersion must be v0.1")
    require(root.get("kind") == "PortableAIRoot", f"{rel}: kind must be PortableAIRoot")
    require(str(root.get("rootId", "")).startswith("urn:srcos:portable-ai-root:"), f"{rel}: rootId must be a SourceOS portable-ai-root URN")
    require(root.get("profileKey") in ALLOWED_PROFILES, f"{rel}: unsupported profileKey")

    dirs = root.get("directories", {})
    for key in ["manifests", "runtimes", "models", "cache", "state", "surfaces", "evidence", "tmp"]:
        require(key in dirs and isinstance(dirs[key], str), f"{rel}: directories.{key} is required")

    surfaces = set(root.get("surfaces", []))
    require(bool(surfaces), f"{rel}: surfaces must be non-empty")
    require(surfaces.issubset(ALLOWED_SURFACES), f"{rel}: unsupported surface declared")

    policy = root.get("policy", {})
    require(policy.get("promptEgressDefault") == "deny", f"{rel}: prompt egress must default deny")
    require(policy.get("runtimeActivation") == "agent-machine-gated", f"{rel}: runtimeActivation must be agent-machine-gated")
    require(policy.get("modelDownloads") == "explicit-only", f"{rel}: modelDownloads must be explicit-only")
    require(policy.get("bindAddressDefault") == "127.0.0.1", f"{rel}: bindAddressDefault must be loopback")

    evidence = root.get("evidence", {})
    require(evidence.get("promptBodiesStored") is False, f"{rel}: prompt bodies must not be stored in evidence")


def main() -> int:
    try:
        load_json(PACK_SCHEMA)
        load_json(ROOT_SCHEMA)
        require(PACK_EXAMPLES, "no ModelCarryPack examples found")
        require(ROOT_EXAMPLES, "no PortableAIRoot examples found")
        for example in PACK_EXAMPLES:
            validate_pack(example, load_json(example))
            print(f"ok: {example.relative_to(ROOT)}")
        for example in ROOT_EXAMPLES:
            validate_root(example, load_json(example))
            print(f"ok: {example.relative_to(ROOT)}")
    except ValidationError as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 1

    print("Portable AI pack validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
