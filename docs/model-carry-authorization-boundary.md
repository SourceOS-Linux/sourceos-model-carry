# Model Carry Authorization Boundary

## Purpose

`ModelCarryAuthorizationBoundary` proves that a SourceOS local model profile is a carry-layer reference object, not an authorization object.

The model carry repo may carry profiles, service refs, launch hints, cache policy, and evidence expectations. It does not authorize prompt egress, network access, tool use, model download, training on user data, model promotion, or model lifecycle mutation.

## Boundary chain

```text
local model profile = carry/reference object
model router = routing decision
policy fabric = prompt egress / network / tool-use admission
model governance ledger = lifecycle, tuning, promotion, consent, revocation evidence
explicit pull/install = separate operator action
```

## Required false authorizations

A valid boundary record must set all of these to `false`:

```text
authorizesPromptEgress
authorizesNetworkAccess
authorizesToolUse
authorizesModelDownload
authorizesTrainingOnUserData
authorizesModelPromotion
authorizesLifecycleMutation
```

## Validation

```bash
python3 tools/validate_model_carry_authorization_boundaries.py
```

The validator checks one valid boundary fixture and negative fixtures for prompt egress and automatic model download.

## Non-goals

This tranche does not implement model execution, router decisions, model download, prompt egress, network access, tool access, personal tuning, or model promotion.

It only hardens the carry-layer contract so future implementation work cannot treat a profile as authorization.
