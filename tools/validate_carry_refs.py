#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
REQUIRED_TOP = {"apiVersion", "kind", "metadata", "spec"}
REQUIRED_SPEC = {"surface", "serviceRef", "client", "launch", "cache", "policy", "evidence", "authority"}
ALLOWED_SURFACES = {
    "speech",
    "ocr",
    "image",
    "video",
    "translation",
    "embedding",
    "timeseries",
    "graph",
    "agent",
    "guardrail",
    "router",
}


def fail(path: Path, message: str) -> int:
    print(f"ERROR: {path}: {message}", file=sys.stderr)
    return 1


def validate(path: Path) -> int:
    data = json.loads(path.read_text())
    missing_top = REQUIRED_TOP - set(data)
    if missing_top:
        return fail(path, f"missing top-level fields: {sorted(missing_top)}")
    if data["apiVersion"] != "modelcarry.sourceos.dev/v1":
        return fail(path, "apiVersion must be modelcarry.sourceos.dev/v1")
    if data["kind"] != "SourceOSCarryRef":
        return fail(path, "kind must be SourceOSCarryRef")

    spec = data["spec"]
    missing_spec = REQUIRED_SPEC - set(spec)
    if missing_spec:
        return fail(path, f"missing spec fields: {sorted(missing_spec)}")
    if spec["surface"] not in ALLOWED_SURFACES:
        return fail(path, f"unknown surface: {spec['surface']}")
    if not spec["serviceRef"].startswith("service://"):
        return fail(path, "serviceRef must be a service:// reference")

    policy = spec["policy"]
    if policy.get("requiresSignedServiceRef") is not True:
        return fail(path, "policy.requiresSignedServiceRef must be true")

    authority = spec["authority"]
    if authority.get("sourceosRole") != "carry-only":
        return fail(path, "authority.sourceosRole must be carry-only")
    if authority.get("platformPromotionRequired") is not True:
        return fail(path, "authority.platformPromotionRequired must be true")
    if authority.get("mayReplaceServiceArtifact") is not False:
        return fail(path, "authority.mayReplaceServiceArtifact must be false")

    launch = spec["launch"]
    if "system" in launch.get("workspaceScopes", []):
        return fail(path, "system workspace is not an allowed AI carry invocation scope")

    client = spec["client"]
    if not client.get("packageRef") or not client.get("entrypoint"):
        return fail(path, "client.packageRef and client.entrypoint are required")

    return 0


def main() -> int:
    files = sorted(EXAMPLES.glob("*-carry-ref.json"))
    if not files:
        print("ERROR: no carry reference examples found", file=sys.stderr)
        return 1
    rc = 0
    for path in files:
        rc = validate(path) or rc
    if rc == 0:
        print(f"OK: validated {len(files)} SourceOS carry references")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
