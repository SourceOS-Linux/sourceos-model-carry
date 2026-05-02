# Local Model Door

The Local Model Door is the SourceOS carry-layer profile for small laptop-safe models used for local routing, triage, summarization, rewriting, Office Plane assist, Agent Machine assist, and offline fallback.

It is not the model lifecycle authority. SourceOS carries service references, launch profiles, cache policy, and evidence expectations. `SocioProphet/model-router` remains the policy-aware routing layer.

## Default profile posture

The default laptop-safe profile is:

```text
urn:srcos:model-profile:local-llama32-1b
```

It targets `llama3.2:1b` through Ollama as a low-memory local router/triage/summarization model.

The higher-quality local fallback is:

```text
urn:srcos:model-profile:local-llama32-3b
```

It targets `llama3.2:3b` for machines that can afford the larger local model.

## Why Llama 3.2 first

The profile uses the Llama 3.2 1B/3B family because it is small enough for laptop use, widely available through local runtimes, and adequate for routing, triage, summarization, rewriting, and low-risk local assist tasks.

This does not hard-code SourceOS to Llama. The schema supports other local model families and runtimes.

## Runtime posture

Initial runtime target:

```text
ollama at http://127.0.0.1:11434
```

Future compatible runtimes:

- `llama.cpp`
- `mlx`
- OpenAI-compatible local servers
- SourceOS-native model service adapters

## Security posture

Default profile policy:

- local-only by default;
- do not send prompts off-device by default;
- do not authorize tool use by default;
- do not authorize network access by default;
- do not download model weights automatically;
- explicit pull/install step required;
- evidence should record availability, runtime health, routing decision, and prompt hash only.

## Intended uses

Good default local uses:

- route between local/hosted model options;
- triage whether a request needs a larger model;
- summarize local files already exposed through Agent Machine or Office Door policy;
- rewrite local drafts;
- assist Office Plane artifact generation;
- provide offline fallback chat;
- provide quick local command-palette responses.

Non-goals:

- autonomous tool execution;
- unsandboxed shell access;
- external web access;
- hidden model download;
- replacing model governance, model promotion, or hosted high-quality model paths.

## Integration path

| Repo | Role |
|---|---|
| `SourceOS-Linux/sourceos-model-carry` | Local model profile contracts and examples. |
| `SocioProphet/model-router` | Policy-aware local-vs-hosted routing. |
| `SourceOS-Linux/sourceos-devtools` | `sourceosctl local-model ...` detection, plan, and evidence. |
| `SourceOS-Linux/agent-term` | Operator events for local model availability and routing requests. |
| `SocioProphet/agentplane` | Evidence artifacts when local model routing/assist participates in governed runs. |

## Current examples

```text
examples/local-model-profile.llama32-1b.json
examples/local-model-profile.llama32-3b.json
```
