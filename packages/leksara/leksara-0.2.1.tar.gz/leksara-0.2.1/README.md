<h1 align="center">LEKSARA</h1>

<p align="center">
  <em>Transforming Text, Empowering Insights Instantly</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/leksara/" style="text-decoration: none;">
    <img src="https://badge.fury.io/py/leksara.svg" alt="PyPI version">
  </a>
  <img src="https://img.shields.io/pypi/pyversions/leksara" alt="PyPI - Python Version">
  <img src="https://img.shields.io/pypi/l/leksara" alt="PyPI - License">
</p>

> Indonesian-language text preparation toolkit for production review pipelines: clean, mask, and normalize in a single pass.

The library ships linguistic resources, preset-driven orchestration, and modular helpers so data teams can audit raw text, remediate sensitive content, and standardize noisy reviews without rebuilding the pipeline from scratch.

---

## Table of Contents

- [Why Leksara](#why-leksara)
- [Quickstart](#quickstart)
- [How Leksara Fits Together](#how-leksara-fits-together)
- [Documentation Map](#documentation-map)
- [Contributing & Support](#contributing--support)

---

## Why Leksara

| Capability | What you get | Key modules |
| --- | --- | --- |
| CartBoard review intake | Dataset audits with PII flags, rating detection, and noise diagnostics ready for dashboards. | `leksara.frames.cartboard` |
| Composable cleaning utilities | Reusable HTML stripping, casing, stopword, emoji, punctuation, and numeric cleanup helpers. | `leksara.function` |
| PII masking & redaction | Regex-backed replacement for Indonesian phones, emails, addresses, and national IDs with configurable modes. | `leksara.pattern` plus `leksara/resources/regex_patterns/` |
| Review-focused normalization | Slang/acronym expansion, contraction repair, rating extraction, and elongation trimming for Bahasa Indonesia. | `leksara.functions.review` |
| ReviewChain orchestrator | `leksara(...)` wrapper and `ReviewChain` class for preset pipelines, benchmarking, and hybrid custom flows. | `leksara.core.chain` |
| Resource-driven customization | Drop in your own dictionaries and regex rules to adapt cleaners for new verticals. | `leksara/resources/` |

Deep dives live in `docs/features.md` alongside API tables, dependencies, and ready-to-run notebooks.

---

## Quickstart

1. **Create and activate a virtual environment**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install leksara
   ```

   Optional extras and troubleshooting tips are documented in `docs/installation.md`.

2. **Clean a review column with the ecommerce preset**

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

   df["clean_text"] = leksara(df["review_text"], preset="ecommerce_review")
   print(df[["review_id", "clean_text"]])
   ```

    | review_id | clean_text |
    | --- | --- |
    | 101 | `barang mantap email [EMAIL] wa [PHONE_NUMBER]` |
    | 102 | `kualitas 4.0 kirim 4.0 hubung [PHONE_NUMBER]` |

4. **Audit raw text with CartBoard**

   ```python
   from leksara.frames.cartboard import get_flags, get_stats

   flags = get_flags(df, text_column="review_text")
   stats = get_stats(df, text_column="review_text")

   print(flags[["review_id", "pii_flag", "rating_flag", "non_alphabetical_flag"]])
   print(stats.iloc[0]["stats"])  # nested histogram of noise sources
   ```

5. **Compose a tailored pipeline with ReviewChain**

   ```python
   from leksara import ReviewChain
   from leksara.function import case_normal, remove_punctuation, remove_stopwords
   from leksara.pattern import replace_email, replace_phone

   chain = ReviewChain.from_steps(
       patterns=[
           (replace_phone, {"mode": "replace"}),
           (replace_email, {"mode": "replace"}),
       ],
       functions=[case_normal, remove_stopwords, remove_punctuation],
   )

   cleaned, metrics = chain.transform(df["review_text"], benchmark=True)
   ```

   `metrics` includes per-step timings so you can spot bottlenecks or confirm PII masks run before downstream cleaners.

---

## How Leksara Fits Together

| Layer | Purpose | Entry points |
| --- | --- | --- |
| Pipelines | High-level orchestration that accepts raw sequences and returns cleaned text plus optional benchmarks. | `leksara(...)`, `ReviewChain` |
| Frames | Review-table utilities for bulk audits and dashboard-friendly stats. | `leksara.frames.cartboard` |
| Functions | Composable cleaning helpers mirrored from the implementation modules. | `leksara.function` |
| Patterns | Opt-in masking utilities with regex rules for PII. | `leksara.pattern` |
| Resources | Dictionaries, regex rules, and whitelists that drive domain knowledge. | `leksara/resources/` |
| Logging & Benchmarking | Optional hooks for throughput tuning and step-level visibility. | `leksara.core.logging`, `benchmark=True` |

Architectural notes, data contracts, and extension points for each layer are captured in `docs/features.md`.

---

## Documentation Map

| Topic | When to read | Location |
| --- | --- | --- |
| Installation & environment | Provisioning a workstation or CI agent | `docs/installation.md` |
| Feature deep dives | Behavioral details, configuration knobs, and dependencies | `docs/features.md` |
| Public API reference | Signatures, argument descriptions, return payloads | `docs/api.md` |
| Worked examples | Copy/paste recipes for notebooks or pipelines | `docs/examples.md` |
| Dependency matrix | Optional packages and enterprise alignment | `docs/dependencies.md` |
| Contributing guide | Environment, style, testing, documentation expectations | `docs/contributing.md` |

---

## Contributing & Support

- Read `docs/contributing.md` before opening a pull request; it outlines environment setup, code style, testing, and documentation requirements.
- File issues on GitHub with reproducible examples, presets used, optional dependencies, and OS details when reporting pipeline differences.
- Commercial or large-scale users should wrap `ReviewChain` with automated smoke tests to detect upstream dictionary or regex changes early.

Leksara is licensed under the terms specified in `LICENSE`.
