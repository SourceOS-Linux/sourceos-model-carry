# SourceOS Model Carry

SourceOS Model Carry defines the on-device carriage layer for governed AI services.

The purpose of this repository is to let SourceOS work like a polished local-first operating system while keeping AI service lifecycle authority outside the mutable workstation image.

## Position

SourceOS may carry:

- service clients;
- launch profiles;
- signed service references;
- local cache policy;
- fallback references;
- ReleaseSet and BootReleaseSet bindings;
- evidence collectors;
- workstation integration hints;
- Local Model Door profiles for laptop-safe local routing and assist models.

SourceOS must not become the authority for model promotion, model lifecycle state, or personal tuning authorization.

## Product goal

The near-term target is an on-device experience that feels as integrated as macOS, but is more open, auditable, local-first, and mesh-ready.

That means:

- fast command-palette and keyboard-first workflow;
- local service discovery;
- offline-safe fallback behavior;
- clear per-service trust and provenance;
- user, project, and agent workspace separation;
- signed service references rather than unmanaged local artifact replacement;
- clean integration with SourceOS shell, boot, and profile systems;
- local model profiles that can serve routing, triage, summarization, rewriting, Office Plane assist, Agent Machine assist, and offline fallback without sending prompts off-device by default.

## Repository scope

This repository contains:

- `contracts/` JSON schemas for SourceOS carry objects;
- `examples/` example local AI service profiles;
- `docs/` architecture and workstation integration guidance;
- `tools/` lightweight validation helpers.

Runtime service implementation belongs in SocioProphet platform service repositories. Lab execution belongs in SociOS Linux lab repositories.

## Local Model Door

The Local Model Door is the carry-layer profile family for laptop-safe local models.

Current examples:

```text
examples/local-model-profile.llama32-1b.json
examples/local-model-profile.llama32-3b.json
```

The default laptop-safe profile is `llama3.2:1b` through Ollama. The quality fallback profile is `llama3.2:3b`.

These profiles are local-only by default. They do not authorize network access, tool use, prompt egress, or automatic model download. Pulling/installing model weights remains explicit.

See:

```text
docs/local-model-door.md
contracts/local-model-profile.schema.json
```

## Personal tuning boundary

Per-user tuning is mandatory as a product direction, but it is not authorized by this carry profile alone.

The correct split is:

| Layer | Responsibility |
|---|---|
| `SourceOS-Linux/sourceos-model-carry` | Carry local model profiles, local service references, and evidence expectations. |
| `SociOS-Linux/socios` | Opt-in orchestration for per-user tuning jobs and data preparation. |
| `SocioProphet/model-governance-ledger` | Personal tuning contracts, consent receipts, dataset lineage, evaluation receipts, promotion decisions, and revocation. |
| `SocioProphet/model-router` | Route between base local model, personally tuned adapter/model, and hosted fallbacks under policy. |

No profile in this repository grants permission to train on user data. Personal tuning requires a separate consented `PersonalTuningContract` and evidence ledger.

## Validation

```bash
python3 tools/validate_local_model_profiles.py
```
