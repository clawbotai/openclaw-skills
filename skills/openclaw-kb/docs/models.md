# Models CLI

## Model selection order
1. Primary model (agents.defaults.model.primary)
2. Fallbacks in agents.defaults.model.fallbacks (in order)
3. Provider auth failover within a provider before next model

## Key config keys
- agents.defaults.model.primary / .fallbacks
- agents.defaults.imageModel.primary / .fallbacks
- agents.defaults.models (allowlist/catalog + aliases)
- models.providers (custom providers → models.json)

## "Model is not allowed"
If agents.defaults.models is set, it becomes the allowlist. Models not in it are rejected with "Model is not allowed" — which looks like the bot didn't respond. Fix: add model to allowlist, clear allowlist, or use /model to pick allowed one.

## Switching models (/model)
```
/model           # compact numbered picker
/model list      # same
/model 3         # select by number
/model openai/gpt-5.2  # by full name
/model status    # detailed view (auth, endpoints)
```

## CLI commands
```
openclaw models list [--all] [--local] [--provider X]
openclaw models status [--check]
openclaw models set <provider/model>
openclaw models set-image <provider/model>
openclaw models aliases list|add|remove
openclaw models fallbacks list|add|remove|clear
```

## Scanning (OpenRouter free models)
`openclaw models scan` — probes free models for tool/image support, ranks by latency/context/params.

## Setup wizard
`openclaw onboard` — sets up model + auth for common providers.

## Quick model picks
- GLM: better for coding/tool calling
- MiniMax: better for writing and vibes
