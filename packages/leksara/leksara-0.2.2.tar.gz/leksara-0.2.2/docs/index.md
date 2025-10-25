# Leksara Documentation

Leksara is an opinionated toolkit for processing Indonesian e-commerce reviews, chat transcripts, and support tickets. It bundles fast heuristics for PII masking, slang normalisation, stopword management, preset pipelines, and dashboard-friendly analytics.

---

## Quick start

1. Install the package and optional extras (see `installation.md`).
2. Instantiate a preset pipeline or build one from individual helpers.
3. Use CartBoard to audit raw text before and after cleaning.
4. Benchmark pipelines in CI to guard against regressions.

```python
from leksara import leksara

sample = ["Email saya user@shop.id ⭐⭐⭐⭐⭐"]
cleaned, metrics = leksara(sample, preset="ecommerce_review", benchmark=True)
print(cleaned[0])
print(metrics)
```

---

## Documentation map

| Topic | Read this first | Complementary references |
| --- | --- | --- |
| Feature deep dives & best practices | `features.md` | `examples.md`, `usage.md` |
| Public APIs & signatures | `api.md` | `features.md`, `dependencies.md` |
| Installation & environment setup | `installation.md` | `dependencies.md`, `usage.md` |
| Preset catalogue | `presets.md` | `features.md` (ReviewChain & preset sections) |
| Practical recipes | `examples.md` | `usage.md`, `benchmarks.md` |
| Benchmarking guidance | `benchmarks.md` | `features.md` (ReviewChain goals) |
| Contribution workflow | `contributing.md` | `tests/` directory, `README.md` |
| Dependency rationale | `dependencies.md` | `installation.md`, `features.md` |

---

## Feature highlights

- **CartBoard dashboards** capture PII, rating mentions, emoji usage, and other noise indicators without mutating raw text.
- **Composable cleaning primitives** provide deterministic behaviour for casing, stopwords, punctuation, links, and emoji.
- **Dedicated pattern layer** isolates PII masking (`leksara.pattern`) so you opt in to heavy regex rules only when needed.
- **Advanced review normalisation** handles rating expressions, slang, acronyms, contractions, and Indo-specific stemming.
- **ReviewChain orchestrators** unify preset and custom pipelines with benchmarking, logging hooks, and whitelist protection.
- **Resource packs** ship bundled dictionaries and regex patterns that you can override at runtime when domain knowledge evolves.

---

## Need more?

- See `README.md` for an overview and badges.
- Join the discussions tab or open an issue if the documentation misses a scenario you care about.
- Contributions are welcome—start with `contributing.md`.

