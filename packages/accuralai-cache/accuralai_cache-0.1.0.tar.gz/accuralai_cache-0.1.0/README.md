# accuralai-cache

`accuralai-cache` provides cache implementations for the AccuralAI pipeline. The initial release ships an in-memory cache with TTL support, statistics, and deterministic cache-key helpers. It registers the `advanced` cache plugin that `accuralai-core` can load automatically.

Install alongside the core orchestrator:

```bash
pip install accuralai-core accuralai-cache
```

Once installed, the CLI pipeline will cache responses in-memory, honoring TTL and capacity limits defined in your configuration.
