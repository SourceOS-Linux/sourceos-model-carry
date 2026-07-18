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
- workstation integration hints.

SourceOS must not become the authority for model promotion or model lifecycle state.

## Product goal

The near-term target is an on-device experience that feels as integrated as macOS, but is more open, auditable, local-first, and mesh-ready.

That means:

- fast command-palette and keyboard-first workflow;
- local service discovery;
- offline-safe fallback behavior;
- clear per-service trust and provenance;
- user, project, and agent workspace separation;
- signed service references rather than unmanaged local artifact replacement;
- clean integration with SourceOS shell, boot, and profile systems.

## Repository scope

This repository contains:

- `contracts/` JSON schemas for SourceOS carry objects;
- `examples/` example local AI service profiles;
- `docs/` architecture and workstation integration guidance;
- `tools/` lightweight validation helpers.

Runtime service implementation belongs in SocioProphet platform service repositories. Lab execution belongs in SociOS Linux lab repositories.
