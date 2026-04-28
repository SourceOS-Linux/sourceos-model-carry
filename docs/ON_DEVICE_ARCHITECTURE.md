# On-Device AI Carry Architecture

## Objective

SourceOS should make local AI services feel native, fast, and integrated without turning the operating system image into an unmanaged model-update channel.

The on-device layer is a carry layer. It carries signed references, clients, launch policy, cache policy, and evidence collectors. It does not own mutable model lifecycle authority.

## On-device product surfaces

### Command and launcher surface

SourceOS should expose AI services through a keyboard-first launcher and command palette.

Examples:

- transcribe selected audio;
- OCR selected file or screenshot;
- summarize selected document;
- translate selected text;
- search personal/project corpus;
- run local embedding update for a project cache;
- launch a governed agent workspace.

### Workspace surface

Every invocation must be scoped to a workspace:

- user workspace;
- project workspace;
- agent workspace;
- system workspace.

System workspace is not a general execution target for AI services.

### Service discovery surface

On-device clients discover services through signed carry references.

A carry reference resolves to:

- service identity;
- endpoint class;
- allowed launch modes;
- required policy;
- cache posture;
- fallback posture;
- evidence requirements.

### Offline and degraded mode

SourceOS may carry offline-safe references and cache policy. It must distinguish:

- online governed service;
- local service;
- cached fallback;
- unavailable service;
- refused service due to policy.

A fallback is valid only if it is signed, pinned, and policy-approved.

## Mac-like but better

The workstation goal is parity with the integrated feel of macOS, not a clone.

Required primitives:

- global command palette;
- consistent keyboard shortcuts;
- service actions on selected files, text, audio, images, and video;
- clipboard and share-sheet style actions through portals;
- local-first index and search;
- clear permission prompts for sensitive actions;
- audit-visible agent and tool activity;
- reproducible profile-driven setup.

The difference from macOS is that every capability should have a visible service reference, provenance, policy, and evidence path.

## SourceOS carry boundary

Allowed:

- client binaries;
- launchers;
- system integration hooks;
- signed carry references;
- local cache indexes;
- cache manifests;
- evidence collectors;
- workspace bindings.

Disallowed:

- unsigned service references;
- ad-hoc artifact replacement;
- unmanaged artifact downloads at boot;
- service promotion from local workstation state;
- agent-controlled model lifecycle changes;
- system-plane mutation for model updates.

## Integration points

- `SourceOS-Linux/sourceos-spec`: normative OS object models.
- `SourceOS-Linux/sourceos-shell`: command palette, shell, and user workflow surface.
- `SourceOS-Linux/sourceos-boot`: ReleaseSet and BootReleaseSet integration.
- `SocioProphet/functional-model-surfaces`: functional AI standards.
- `SocioProphet/prophet-platform`: governed platform services.
- `SociOS-Linux/*lab`: lab execution and candidate artifacts.

## First demo slice

1. Install SourceOS carry examples for speech, OCR, image, video, translation, and embedding.
2. Expose them through a local service listing command.
3. Validate that all carry refs are signed-reference shaped and do not embed mutable artifact authority.
4. Emit evidence for the service list and policy check.
5. Fail validation for an example that attempts to grant model lifecycle authority to SourceOS.
