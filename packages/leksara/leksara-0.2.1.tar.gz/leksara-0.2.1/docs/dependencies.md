# Dependency Guide

This document enumerates the packages Leksara depends on, how each feature uses them, and which extras to install for development or benchmarking. For authoritative version constraints refer to `pyproject.toml`.

---

## Runtime dependencies

| Package | Minimum version | Purpose | Primary features affected |
| --- | --- | --- | --- |
| `pandas` | 1.5 | Provides Series/DataFrame abstractions, vectorised operations, and output structures for `CartBoard` and pipeline helpers. | `leksara(...)`, `ReviewChain.transform`, `CartBoard` utilities. |
| `regex` | 2022.1.18 | Supplies advanced regex syntax (named sets, possessive quantifiers) needed for PII and rating detectors. | `replace_phone`, `replace_address`, `replace_rating`, `get_flags`, `noise_detect`. |
| `emoji` | 2.0.0 | Enables robust emoji detection and replacement. | `remove_emoji`, `CartBoard` noise statistics, review benchmarks. |
| `Sastrawi` | 1.0.1 | Indonesian stemming/lemmatisation engine used by `word_normalization`. | Review normalisation pipelines and presets relying on stemming. |

All runtime dependencies are required; omitting them will either prevent import or degrade functionality significantly. When packaging your own application, pin to specific versions to maintain reproducibility.

---

## Feature-to-dependency matrix

| Feature | pandas | regex | emoji | Sastrawi | Notes |
| --- | --- | --- | --- | --- | --- |
| CartBoard (`get_flags`, `get_stats`, `noise_detect`) | ✅ | ✅ | ✅ | – | `get_stats` benefits from `emoji` for accurate counts but still runs without it (emojis counted as 0). |
| Cleaning primitives (`remove_*`, `replace_url`) | – | ✅ | ✅ | – | Basic cleaners operate with the standard library but produce richer results with `regex`/`emoji`. |
| PII masking (`replace_phone`, `replace_address`, etc.) | – | ✅ | – | – | Regex features power validation and component matching. |
| Review normalisation (`replace_rating`, `shorten_elongation`, `normalize_slangs`, `word_normalization`) | – | ✅ | ✅ | ✅ | `word_normalization` requires `Sastrawi`; other helpers run without it. |
| Presets (`ecommerce_review`) | ✅ | ✅ | ✅ | ✅ | Presets compose functions that rely on the full stack. |
| ReviewChain & benchmarking | ✅ | ✅ | Optional | Optional | Benchmarking uses only standard modules but pipelines inherit dependency requirements. |

✅ indicates the feature requires the dependency to deliver full functionality.

---

## Optional extras

| Extra group | Command | Included packages | Use case |
| --- | --- | --- | --- |
| `dev` | `pip install -e .[dev]` | `pytest`, `pytest-cov`, `ruff`, `mypy`, `build`, `twine`, `ipykernel` | Local development, CI linting, publishing workflows. |
| `docs` | `pip install -e .[docs]` | `mkdocs`, `mkdocs-material` | Building documentation sites. |
| `test` | `pip install -e .[test]` | `pytest`, `pytest-cov` | Minimal test environment without linting or packaging tools. |
| `benchmark` | `pip install -e .[benchmark]` | `tqdm`, `tabulate` | Adds progress bars and tabular formatting for performance studies. |

Combine extras as needed, for example `pip install -e .[dev,benchmark]` when profiling in development.

---

## Python compatibility

Leksara supports Python 3.9 through 3.12. Verify compatibility in your environment:

```bash
python -c "import sys; from leksara import __version__; print(sys.version, __version__)"
```

When distributing across heterogeneous environments (e.g., Airflow workers, Spark executors) ensure all nodes run a supported Python version and have consistent dependency pins.

---

## Verifying installations

- Inspect resolved versions:

```bash
pip show leksara pandas regex emoji Sastrawi
```

- Run smoke tests:

```bash
pytest leksara/tests/test_patterns_pii.py -q
```

- Confirm optional extras if needed:

```bash
pip show mkdocs || echo "docs extra not installed"
```

Document the output in deployment runbooks to simplify auditing and upgrades.


