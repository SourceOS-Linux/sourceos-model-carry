# SourceOSModelCarryRef

Status: additive carry-layer projection fixture

## Purpose

`SourceOSModelCarryRef` is the SourceOS typed-contract projection for an approved on-device reference to a governed model or model-service profile. It complements the existing `SourceOSCarryRef` service reference examples and the existing `LocalModelProfile` laptop-safe local model profiles.

The object is intentionally reference-only. It must not embed mutable model weights, mutable adapters, credentials, user tuning data, or runtime authorization grants.

## Current fixture

```text
examples/sourceos-model-carry-ref.local-llama32-3b.json
```

This fixture links the local `llama32-3b` style profile into the broader Prophet Foundry path:

```text
model-governance-ledger
→ model-router
→ sourceos-model-carry
→ agent-machine
→ agentplane
```

## Validation

Run:

```bash
python3 tools/validate_sourceos_model_carry_refs.py
```

The validator checks:

- `type == SourceOSModelCarryRef`
- `id` uses `urn:srcos:model-carry-ref:`
- `specVersion == 2.1.0`
- `governanceRef` is present
- `routerProfileRef` uses `urn:srcos:model-router-profile:`
- `mutableModelState` is false
- release and fallback references use the expected URN namespaces

## Boundary rules

1. A carry reference is not a model promotion decision.
2. A carry reference is not a runtime route decision.
3. A carry reference is not a permission grant.
4. SourceOS may carry approved references, cache policy, launch profile references, fallback references, and evidence references.
5. SourceOS must not become authority for model lifecycle, model promotion, personal tuning authorization, or runtime side effects.

## Follow-up

After the SourceOS projection contracts stabilize, this validator should be wired into the default `make validate` target alongside existing carry-reference and CLI checks.
