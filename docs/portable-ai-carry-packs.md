# Portable AI Carry Packs

Portable AI Carry Packs are SourceOS model-carry manifests for USB/SSD-local AI kits.

They translate a simple product promise — carry a private local AI workstation on portable storage — into governed SourceOS model-carry objects with provenance, licensing, hash pinning, model-role constraints, runtime compatibility, cache policy, and evidence expectations.

## Boundary

This repository owns the manifest and validation layer. It does not download weights, launch runtimes, run inference, train models, or authorize personalization.

| Layer | Responsibility |
| --- | --- |
| `SourceOS-Linux/sourceos-model-carry` | Portable model-pack contracts, examples, provenance expectations |
| `SourceOS-Linux/sourceos-devtools` | `sourceosctl portable-ai ...` preflight, prepare, inspect, and launch-plan commands |
| `SourceOS-Linux/agent-machine` | Runtime provider activation, residency, cache, teardown, and evidence receipts |
| `SocioProphet/model-router` | Policy-aware local/hosted/personal model routing |
| `SocioProphet/model-governance-ledger` | Consent, tuning, evaluation, promotion, revocation, lineage |
| `SocioProphet/policy-fabric` | Prompt egress, host-write, network, tool, and side-effect policy |

## Manifest families

Portable AI Kit uses two carry-layer object families.

### PortableAIRoot

Describes the portable root itself:

- root id;
- layout version;
- target filesystem expectations;
- evidence directories;
- allowed runtime directories;
- host-write policy;
- zero-trace policy;
- compatible surfaces;
- model-pack refs.

### ModelCarryPack

Describes one curated or BYOM model pack:

- pack id and display name;
- model source and license;
- runtime compatibility;
- expected RAM and disk footprint;
- quantization;
- SHA-256 hash or pending hash requirement;
- task classes;
- safety posture;
- allowed network state;
- local-only default;
- explicit download/import requirement;
- evidence expectations.

## Initial built-in profiles

| Profile | Role | Minimum free space | Suggested models | Default policy |
| --- | --- | --- | --- | --- |
| `tiny-router` | routing, triage, rewrite | 8 GB | 1B/3B class | local-only, no tools |
| `laptop-safe` | offline fallback, basic chat, office assist | 16 GB | 3B/4B class | local-only, no prompt egress |
| `office-local` | summarization and artifact drafting | 32 GB | 3B/7B class | workroom-scoped |
| `code-local` | local coding and repo triage | 32 GB | 7B coding class | repo-scoped |
| `field-kit` | portable SSD operator kit | 64 GB | mixed small + quality fallback | evidence-first |
| `byom-gguf` | custom GGUF import | varies | user supplied | hash + license required |

## Required manifest fields

A `ModelCarryPack` must include:

```json
{
  "type": "ModelCarryPack",
  "apiVersion": "sourceos.model-carry/v1alpha1",
  "id": "urn:srcos:model-carry-pack:laptop-safe-llama32-3b",
  "displayName": "Laptop-safe Llama 3.2 3B",
  "model": {
    "name": "llama3.2:3b",
    "family": "llama",
    "parameterClass": "3b",
    "quantization": "runtime-managed",
    "format": "ollama-ref"
  },
  "runtimeCompatibility": ["ollama-compatible", "openai-compatible-local"],
  "footprint": {
    "minimumFreeGb": 16,
    "recommendedFreeGb": 32,
    "minimumRamGb": 8,
    "recommendedRamGb": 16
  },
  "provenance": {
    "sourceKind": "runtime-catalog",
    "sourceUrl": "ollama://llama3.2:3b",
    "licenseRef": "model-license-required",
    "sha256": null,
    "sha256RequiredBeforeEligibility": true
  },
  "taskClasses": ["summarization", "rewrite", "office-assist", "offline-fallback"],
  "policy": {
    "localOnlyDefault": true,
    "promptEgressDefault": "deny",
    "allowToolUseDefault": false,
    "allowNetworkDefault": false,
    "requiresExplicitImport": true,
    "requiresEvidence": true
  }
}
```

## BYOM GGUF import rules

BYOM is supported, but not as an unmanaged URL paste.

A BYOM pack is not route-eligible until:

1. the file exists under the portable root or approved local source;
2. SHA-256 is computed and stored in evidence;
3. source URL or local source note is recorded;
4. license/refusal-to-attest state is explicit;
5. task classes are operator-selected;
6. prompt-egress and tool-use policy remains denied unless separately granted;
7. model-router receives an eligible model ref, not a raw path.

## Safety posture

SourceOS should not brand packs as "uncensored" or promise universal compliance. The product value is local control, privacy, provenance, and policy-governed autonomy, not removal of safety constraints.

Pack labels should be operational:

- `local-only`;
- `offline-fallback`;
- `coding`;
- `office`;
- `multilingual`;
- `low-memory`;
- `quality-fallback`;
- `byom-unverified`;
- `byom-verified`.

## Evidence expectations

Portable model-carry operations should emit or reference:

- `PortablePreflightEvidence`;
- `ModelCarryPackVerificationEvidence`;
- `BYOMImportEvidence`;
- `RuntimeActivationEvidence`;
- `RouteDecisionEvidence`;
- `PortableWipeEvidence`.

Prompt bodies must not be stored in these evidence records. Prompt hashes and governance refs are sufficient.

## Promotion path

After the v1alpha1 schemas stabilize here, promote canonical contracts to `SourceOS-Linux/sourceos-spec` and keep examples in this repository as installable profile references.
