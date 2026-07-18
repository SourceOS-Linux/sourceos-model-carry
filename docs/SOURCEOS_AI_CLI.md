# sourceos-ai CLI

`sourceos-ai` is the on-device AI carry client for SourceOS.

It validates signed-reference-shaped service carry manifests, lists available governed AI service references, and emits local evidence about what the device can invoke. It does not promote models, replace service artifacts, or own mutable model lifecycle state.

## Command contract

```bash
sourceos-ai --version
sourceos-ai doctor --refs examples
sourceos-ai self-test --refs examples
sourceos-ai emit-evidence --refs examples
sourceos-ai carry list --refs examples
sourceos-ai carry validate --refs examples
sourceos-ai carry doctor --refs examples
```

## Build and validation

```bash
make build
make test
make validate
make dist
make release-dry-run
```

`make validate` runs both the legacy Python carry-ref validator and the compiled `sourceos-ai` validation path.

## Carry-only invariant

Every valid carry reference must satisfy:

- `policy.requiresSignedServiceRef == true`
- `authority.sourceosRole == carry-only`
- `authority.platformPromotionRequired == true`
- `authority.mayReplaceServiceArtifact == false`
- no `system` workspace invocation scope

This keeps SourceOS in the correct product role: clients, launch profiles, cache policy, signed service references, and evidence collectors only.

## Prophet CLI delegation

`prophet-cli` should delegate these command families to `sourceos-ai`:

```bash
prophet sourceos carry list
prophet sourceos carry validate
prophet sourceos carry doctor
prophet sourceos carry emit-evidence
```

## Homebrew target

The future Homebrew formula should install the `sourceos-ai` binary and run a formula test equivalent to:

```bash
sourceos-ai --version
sourceos-ai self-test --refs examples
```
