# accuralai-canonicalize

`accuralai-canonicalize` provides canonicalization utilities and plugins used by the AccuralAI pipeline. The default plugin normalizes prompts, tags, and metadata, and generates deterministic cache keys so downstream stages receive consistent inputs.

Install alongside `accuralai-core` to enable the `standard` canonicalizer:

```bash
pip install accuralai-core accuralai-canonicalize
```

After installation the `accuralai-core` CLI will automatically use the canonicalizer when you run:

```bash
accuralai-core generate --prompt "Hello there!"
```
