# Leksara
[![PyPI version](https://badge.fury.io/py/leksara.svg)](https://pypi.org/project/leksara/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/leksara)
![PyPI - License](https://img.shields.io/pypi/l/leksara)

Leksara is an Indonesian-language text preparation toolkit for data teams who need production-ready cleaning, masking, and normalization pipelines. The library bundles linguistic resources, a preset-driven orchestration layer, and modular helpers so you can audit raw text, remediate sensitive content, and standardize noisy reviews without rebuilding the stack for every project.

---

## Feature Highlights

- **CartBoard review intake** – Inspect raw datasets from chatbots or marketplaces, generate column-level flags (PII, non-alphabetical noise, ratings), and capture metadata for monitoring.
- **Composable cleaning utilities** – `leksara.function` re-exports the building blocks (HTML stripping, casing, stopwords, punctuation, emoji, numeric cleanup) for ad-hoc preprocessing.
- **PII masking and redaction** – Regex-backed detectors for Indonesian phone numbers, emails, addresses, and national IDs with configurable replacement modes and conflict handling.
- **Review-focused normalization** – Slang and acronym expansion, contraction repair, elongated text trimming, rating extraction, stemming/normalization tuned for Bahasa Indonesia.
- **ReviewChain orchestrator** – Run pipelines functionally with `leksara(...)` or via the `ReviewChain` class, mix presets with custom steps, and benchmark per-stage performance.
- **Resource-driven customization** – Ship your own dictionaries and regex rules or extend the bundled JSON/CSV files to adapt the cleaner to new verticals.

Deep dives for each module live in `docs/features.md` together with API tables, dependencies, and ready-to-run recipes.

---

## Quickstart

### 1. Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install leksara
```

Optional extras and troubleshooting tips are listed in `docs/installation.md`.

### 2. Clean a review column in-place

```python
import pandas as pd
from leksara import leksara

df = pd.DataFrame(
    {
        "review_id": [101, 102],
        "review_text": [
            "<p>Barangnya mantul!!! Email saya user@mail.id, WA 0812-3456-7890</p>",
            "Kualitasnya ⭐⭐⭐⭐, pengiriman 4/5. Hubungi +62 812 8888 7777",
        ],
    }
)

# Apply the ecommerce review preset
df["clean_text"] = leksara(df["review_text"], preset="ecommerce_review")
print(df[["review_id", "clean_text"]])
```

### 3. Audit raw text with CartBoard

```python
from leksara.frames.cartboard import get_flags, get_stats

flags = get_flags(df, text_column="review_text")
stats = get_stats(df, text_column="review_text")

print(flags[["review_id", "pii_flag", "rating_flag", "non_alphabetical_flag"]])
print(stats.iloc[0]["stats"])  # nested histogram of noise sources
```

### 4. Compose a tailored pipeline

```python
from leksara import ReviewChain
from leksara.function import (
    case_normal,
    remove_punctuation,
    remove_stopwords,
    replace_email,
    replace_phone,
)

chain = ReviewChain.from_steps(
    patterns=[(replace_phone, {"mode": "replace"}), (replace_email, {"mode": "replace"})],
    functions=[case_normal, remove_stopwords, remove_punctuation],
)

cleaned, metrics = chain.transform(df["review_text"], benchmark=True)
```

---

## Documentation Map

| Topic | When to read | Location |
| --- | --- | --- |
| Installation & environment | You are provisioning a workstation or CI agent | `docs/installation.md` |
| Feature deep dives | You need behavioral details, configuration knobs, or per-feature dependencies | `docs/features.md` |
| Public API reference | You want signatures, argument descriptions, and return payload formats | `docs/api.md` |
| Worked examples | You prefer copy/paste recipes for notebooks or pipelines | `docs/examples.md` |
| Dependency matrix | You must vet optional packages or align with enterprise policies | `docs/dependencies.md` |
| Contributing | You plan to submit patches, run tests, or build docs | `docs/contributing.md` |

---

## How Leksara Fits Together

- **Pipelines** – `leksara(...)` is a convenience wrapper around `ReviewChain`; both accept raw sequences (list/Series) and return cleaned text plus optional benchmarking details.
- **Frames layer** – `CartBoard` and friends operate on review tables, deriving flags, statistics, and noise diagnostics suitable for dashboards.
- **Functions layer** – The `leksara.function` module mirrors the implementation modules under `leksara/functions` so you can cherry-pick individual cleaners without touching internals.
- **Resources** – Regex rules and dictionaries stored under `leksara/resources/` drive PII detection, slang resolution, and whitelist protection. Update these files to specialise the toolkit.
- **Logging & benchmarking** – `leksara.core.logging` ships opt-in helpers to emit step-level logs, while `benchmark=True` collects timing metadata for throughput tuning.

Architectural notes, data contracts, and extension points for each layer are captured in `docs/features.md`.

---

## Contributing & Support

- Read `docs/contributing.md` before opening a pull request. It covers environment setup, style, testing, and documentation requirements.
- File issues on GitHub with reproducible examples; include the preset, optional dependencies, and OS details when reporting pipeline differences.
- Commercial or large-scale users should build automated smoke tests around `ReviewChain` to detect upstream dictionary or regex changes.

Leksara is licensed under the terms specified in `LICENSE`.
