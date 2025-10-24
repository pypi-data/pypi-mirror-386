# accuralai-router

`accuralai-router` provides pluggable routing strategies for the AccuralAI orchestration core. Routers map canonicalized requests to backend identifiers using deterministic policies, weighted load balancing, failover rules, or metadata-aware predicates.

## Features

- Async routers that satisfy the `Router` protocol from `accuralai-core`.
- Direct routing honoring request hints or configured defaults.
- Weighted distribution with deterministic seeding and optional per-backend capacity limits.
- Health-aware failover that cycles through fallback backends.
- Rules engine that matches tags, metadata, or parameter values.

Install alongside the core orchestrator:

```bash
pip install accuralai-core accuralai-router
```

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e packages/accuralai-core[dev]
pip install -e packages/accuralai-router[dev]
pytest packages/accuralai-router/tests -q
```

Routers register entry points under `accuralai_core.routers` so `accuralai-core` can discover them automatically.
