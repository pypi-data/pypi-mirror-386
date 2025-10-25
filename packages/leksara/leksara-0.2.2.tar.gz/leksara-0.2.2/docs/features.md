# Feature Guide

This guide walks through each major surface of Leksara: what problem it solves, which public APIs to call, how the feature behaves with real-world data, and which resources or dependencies it relies on. Each section links back to recipes and reference material so you can jump straight into implementation.

---

## Table of Contents

1. [CartBoard review intake](#cartboard-review-intake)
2. [Cleaning primitives (`functions.cleaner.basic`)](#cleaning-primitives-functionscleanerbasic)
3. [PII masking & redaction (`functions.patterns.pii`)](#pii-masking--redaction-functionspatternspii)
4. [Review normalization (`functions.review.advanced`)](#review-normalization-functionsreviewadvanced)
5. [ReviewChain & `leksara` orchestrators](#reviewchain--leksara-orchestrators)
6. [Preset catalog (`core.presets`)](#preset-catalog-corepresets)
7. [Logging, benchmarking, and observability](#logging-benchmarking-and-observability)
8. [Resource packs & customization](#resource-packs--customization)
9. [Interoperability tips](#interoperability-tips)

---

## CartBoard review intake

### CartBoard goals

Produce fast health checks for raw Indonesian text streams before or after cleaning. CartBoard turns chat logs, marketplace reviews, and survey feedback into structured insights (flags, statistics, noise inventories) suitable for dashboards.

### Primary entry points

| API | Description | Output |
| --- | --- | --- |
| `CartBoard(raw_text: str, rating: float \| int \| None = None)` | Lightweight dataclass capturing a single review plus computed flags. | `.to_dict()` returns `original_text`, `rating`, `pii_flag`, `non_alphabetical_flag`. |
| `get_flags(data, *, text_column="text", non_alpha_threshold=0.15, merge_input=True)` | Vectorised boolean flags for PII, rating mentions, and non-alphabetical noise. Accepts `str`, list, `Series`, or `DataFrame`. | `DataFrame` with original data (when `merge_input=True`) plus derived flag columns. |
| `get_stats(data, *, merge_input=True, as_dict=True, text_column="text")` | Length, word-count, Indonesian stopword hits, emoji count, whitespace metrics. | When `as_dict=True` each row holds a `dict` under `stats`; set to `False` to expand into columns. |
| `noise_detect(data, *, include_normalized=True, merge_input=True, text_column="text")` | Enumerates raw URLs, HTML tags, emails, phones, emojis and optionally normalized phone numbers. | `DataFrame` with a `detect_noise` column holding dictionaries for every row. |

### Supported inputs

- `str`: treated as a single review entry.
- `Iterable[str]`: returns a frame without the original index.
- `pandas.Series`: index is preserved; column name used as fallback when `text_column` is not provided.
- `pandas.DataFrame`: use `text_column` to point to the text field; the function keeps other columns if `merge_input=True`.

### Dependencies

- `pandas` (core dependency) for DataFrame/Series operations.
- `regex`, `emoji`, and the bundled dictionaries drive detection accuracy.

### Usage sequence

```python
import pandas as pd
from leksara.frames.cartboard import get_flags, get_stats, noise_detect

reviews = pd.DataFrame(
    {
        "review_id": [1, 2, 3],
        "text": [
            "Barang mantul!!! Email: user@example.com, ⭐ 5/5",
            "Pengiriman lambat :( hubungi 081234567890",
            "Produk ok.",
        ],
    }
)

flags = get_flags(reviews, text_column="text")
stats = get_stats(reviews, text_column="text")
noise = noise_detect(reviews, text_column="text", include_normalized=False)

print(flags[["review_id", "pii_flag", "rating_flag", "non_alphabetical_flag"]])
print(stats.iloc[0]["stats"]["stopwords"])
print(noise.iloc[1]["detect_noise"]["phones"])
```

### Operational notes

- `non_alpha_threshold` controls how tolerant the detector is to symbols and ASCII art. Lower thresholds catch more cases but may flag legitimate product names.
- CartBoard does not mutate text; use it in read-only audits before invoking cleaning pipelines.
- Combine `get_flags` with cleaning outputs to confirm that PII masking removed flagged tokens.
- Stopword counts reflect the bundled Indonesian dictionary; pass a custom iterable to `remove_stopwords` (or pre-clean text) when you need domain-specific vocabularies.

---

## Cleaning primitives (`functions.cleaner.basic`)

### Cleaning goals

Provide modular building blocks for baseline normalization. Each function is stateless and can be used individually or inside a `ReviewChain` pipeline.

### Module import

```python
from leksara.function import (
    remove_tags,
    case_normal,
    remove_stopwords,
    remove_whitespace,
    remove_punctuation,
    remove_digits,
    remove_emoji,
    replace_url,
)
```

### Function catalogue

| Function | Description | Key parameters | Notes |
| --- | --- | --- | --- |
| `remove_tags(text)` | Strips HTML/XML tags and decodes common entities. | – | Uses regex patterns tuned for marketplace review markup. |
| `case_normal(text)` | Lowercases text and normalises accented characters & punctuation width. | – | Maintains placeholder brackets (`[TOKEN]`). |
| `remove_stopwords(text, stopwords: Iterable[str] \| None = None)` | Drops Indonesian stopwords. | `stopwords`: override or extend bundled list. | Falls back to `resources/stopwords/id.txt` when `None`. |
| `remove_whitespace(text)` | Collapses repeated whitespace and trims ends. | – | Safe to use after masking to avoid destroying placeholder spacing. |
| `remove_punctuation(text)` | Removes punctuation characters except underscore and placeholders. | – | Handles full-width punctuation and emoji punctuation. |
| `remove_digits(text)` | Removes decimal digits. | – | Combine with `replace_rating` if you still need rating tokens. |
| `remove_emoji(text)` | Drops emoji code points. | – | Requires `emoji` package for best coverage; silently skips when missing. |
| `replace_url(text, mode="remove"\|"replace", placeholder="[URL]")` | Detects URLs (with or without protocol) and removes or masks them. | `mode`, `placeholder` | Relies on `URL_PATTERN` definitions in `basic.py`. |

### Pipeline example

```python
from leksara.function import (
    remove_tags,
    case_normal,
    remove_stopwords,
    remove_punctuation,
    remove_whitespace,
)

text = "<p>Pengiriman CEPAT banget, tapi kemasan ?!? masih kurang</p>"
cleaned = remove_whitespace(
    remove_punctuation(
        remove_stopwords(
            case_normal(
                remove_tags(text)
            )
        )
    )
)
```

### Customization tips

- Provide an explicit stopword list to `remove_stopwords` when working with domain-specific jargon (e.g., fintech, mobility); the function merges your iterable with the default set.
- Use `replace_url` in `mode="replace"` before `remove_punctuation` to preserve link positions for post-processing analytics.
- Place `remove_digits` late in the pipeline if you also care about rating expressions—otherwise `replace_rating` may not see numeric tokens.

---

## PII masking & redaction (`functions.patterns.pii`)

### PII protection goals

Detect and obfuscate personally identifiable information common in Indonesian commerce chat flows: phone numbers, emails, addresses, and national IDs (NIK).

### Import surface

```python
from leksara.pattern import (
    replace_phone,
    replace_address,
    replace_email,
    replace_id,
)
```

### Modes & defaults

| Function | Default mode | Placeholder | Notes |
| --- | --- | --- | --- |
| `replace_phone(text, mode="remove"\|"replace")` | `remove` | `[PHONE_NUMBER]` | Normalises `+62`, `62`, and `0` prefixes; validates length (10–13 digits). |
| `replace_email(text, mode="remove"\|"replace")` | `remove` | `[EMAIL]` | Case-insensitive regex handles plus aliases and subdomains. |
| `replace_address(text, mode="remove"\|"replace", **kwargs)` | `remove` | `[ADDRESS]` | Uses trigger phrases from `dictionary_rules.json`; accepts component toggles (`rtrw=True`, `postal_code=True`, etc.). |
| `replace_id(text, mode="remove"\|"replace")` | `remove` | `[NIK]` | Matches 16-digit Indonesian national IDs with optional spacing. |

### Component selection for addresses

`replace_address` reads component definitions from `resources/regex_patterns/pii_patterns.json`. Pass keyword arguments to restrict masking to certain fields:

```python
replace_address(text, mode="replace", street=True, rtrw=False, city=True)
```

If you pass an unknown component name, the function raises a `KeyError`. Use `replace_address.__doc__` or inspect the JSON file to discover valid keys.

### Example: secure chat transcript

```python
from leksara.pattern import replace_phone, replace_email, replace_address

text = (
    "Halo, nama saya Rani. Email: rani+vip@contoh.co.id, "
    "alamat: Jl. Melati No. 12 RT 03 RW 05, Bandung. Telepon (0812) 345-6789"
)

masked = replace_address(
    replace_email(
        replace_phone(text, mode="replace"),
        mode="replace",
    ),
    mode="replace",
)
```

### Failure handling

- Non-string inputs raise `TypeError` to prevent silent failures in data pipelines.
- The regex configuration is loaded once on module import. If the JSON resources cannot be read, the module logs the error and all replacements become no-ops—monitor logs in production environments.

---

## Review normalization (`functions.review.advanced`)

### Normalization goals

Standardise Indonesian review language so downstream models receive canonical, analysable tokens. The focus is on ratings, expressive spelling, slang, acronyms, contractions, and stemming.

### Key functions

| Function | Purpose | Configuration knobs | Backing data |
| --- | --- | --- | --- |
| `replace_rating(text, placeholder="__RATING_5__" …)` | Detects `5/5`, star emojis, verbal scores (“lima bintang”) and converts them into numeric or placeholder tokens. | `placeholder`, `normalize_scale=True` to map arbitrary scales into 0–5. | `resources/regex_patterns/rating_patterns.json`, `rating_rules.json`. |
| `shorten_elongation(text, max_repeat=2)` | Compresses repeated characters to mitigate expressive elongation (`mantuuulll`). | `max_repeat` must be ≥1. | Self-contained regex. |
| `replace_acronym(text, mode="replace"\|"remove")` | Expands or removes acronyms. Applies context-aware conflict rules (e.g., “m” → “meter” vs “medium”). | `mode`. | `resources/dictionary/acronym_dict.json`, `dictionary_rules.json`. |
| `normalize_slangs(text, mode="replace"\|"remove")` | Substitutes slang with standard words. | `mode`; fallback to original when dictionary missing. | `resources/dictionary/slangs_dict.json`. |
| `expand_contraction(text)` | Expands Indonesian contractions (“gk” → “tidak”). | – | `resources/dictionary/contractions_dict.json`. |
| `word_normalization(text, method="stem", word_list=None, mode="keep")` | Applies stemming/lemmatisation while protecting placeholders. | `method`, `word_list`, `mode` (`keep`, `only`, `exclude`). | `Sastrawi` stemmer plus whitelist management. |

### Common recipe

```python
from leksara.function import (
    replace_rating,
    shorten_elongation,
    normalize_slangs,
    replace_acronym,
    word_normalization,
)

text = "Mantuuul ⭐⭐⭐⭐⭐ abis! CS nya grg bgt tp overall 4/5"
normalized = word_normalization(
    replace_acronym(
        normalize_slangs(
            shorten_elongation(
                replace_rating(text)
            )
        )
    ),
    mode="keep",
)
```

### Best practices

- Run `replace_rating` before removing digits so that ratios (`4/5`) are still present.
- Detect and expand slang before stemming; otherwise the stemmer might produce unexpected roots.
- Preserve placeholders by keeping `mode="keep"` in `word_normalization`; the helper automatically masks `[TOKEN]` segments while calling the stemmer.
- When `Sastrawi` is not installed, `word_normalization` returns the input text unchanged—plan optional dependency validation accordingly.

---

## ReviewChain & `leksara` orchestrators

### Orchestration goals

Provide consistent execution semantics for cleaning pipelines whether you prefer functional or object-oriented APIs.

### Two ways to run pipelines

| Option | When to choose | Signature |
| --- | --- | --- |
| `leksara(data, pipeline=None, preset=None, *, benchmark=False)` | Quick transforms in notebooks or scripts; no need to manage object state. | Returns cleaned data (list or Series). When `benchmark=True`, returns `(cleaned, metrics)`. |
| `ReviewChain` | You need to reuse the same steps many times, inspect intermediate names, or embed in services. | Construct via `ReviewChain.from_steps(patterns, functions)` or `.from_preset(name)`. Methods: `.transform(data, benchmark=False)`, `.process_text(text)`, `.run_on_series(series)`. |

### Pipeline schema

Import helpers explicitly from their respective modules before constructing the schema:

```python
from leksara.pattern import replace_phone, replace_email
from leksara.function import case_normal, remove_stopwords, remove_punctuation
```

```python
pipeline = {
    "patterns": [
        (replace_phone, {"mode": "replace"}),
        (replace_email, {"mode": "replace"}),
    ],
    "functions": [
        case_normal,
        remove_stopwords,
        remove_punctuation,
    ],
}

# Functional
cleaned_reviews = leksara(reviews, pipeline=pipeline)

# Object oriented
chain = ReviewChain.from_steps(**pipeline)
cleaned_reviews, metrics = chain.transform(reviews, benchmark=True)
```

### Benchmark payload

When `benchmark=True`, both APIs return a dictionary:

```python
{
    "n_steps": 5,
    "total_time_sec": 0.004,
    "per_step": [
        ("replace_phone", 0.0009),
        ("replace_email", 0.0007),
        ...
    ],
}
```

## Preset catalog (`core.presets`)

Presets are opinionated combinations of pattern detectors and cleaning functions. They live in `leksara/core/presets.py` and provide reproducible pipelines for common Indonesian review scenarios.

### Usage

```python
from leksara import leksara
from leksara.core.presets import get_preset

print(get_preset("ecommerce_review"))
cleaned = leksara(data, preset="ecommerce_review")
```

### Extending presets

```python
preset = get_preset("ecommerce_review")
custom = {
    "patterns": preset["patterns"] + [(replace_address, {"mode": "replace"})],
    "functions": preset["functions"] + [remove_digits],
}

cleaned = leksara(data, pipeline=custom)
```

Refer to the preset definition to learn which optional dependencies it expects (e.g., Sastrawi for word normalization). Document these requirements in your internal runbooks if you redistribute presets to other teams.

---

## Logging, benchmarking, and observability

- `leksara.core.logging.setup_logging()` configures console and file handlers aligned with the project’s `logging` defaults (`pipeline.log` in repo root). Use it in services to trace pipeline execution.
- `log_pipeline_step(preset_name, raw_text, processed_text)` records per-review diffs for auditing. Useful in regulated environments where you must prove how sensitive data was redacted.
- Benchmark outputs (see above) are deterministic and can be asserted in regression tests to guard against performance regressions.

---

## Resource packs & customization

The `leksara/resources/` directory stores dictionaries and pattern files that power detection accuracy. They are bundled in the Python package, but you can extend or override them at runtime.

| Resource | File | Purpose | Customization strategy |
| --- | --- | --- | --- |
| Stopwords | `stopwords/id.txt` | Default Indonesian stopword list for `remove_stopwords`. | Append additional terms via `remove_stopwords(text, stopwords=set([...]))`. |
| Slang dictionary | `dictionary/slangs_dict.json` | Maps slang to canonical words. | Load JSON, update map, monkeypatch `_SLANGS_DICT`. |
| Acronym rules | `dictionary/acronym_dict.json`, `dictionary_rules.json` | Expansions and conflict patterns used by `replace_acronym`. | Extend JSON and reload module, or supply custom function in pipeline. |
| PII patterns | `regex_patterns/pii_patterns.json`, `dictionary_rules.json` | Phone/address/email/NIK regex definitions. | Fork the JSON file, then set environment variable or patch loader before import. |
| Rating patterns | `regex_patterns/rating_patterns.json`, `rating_rules.json` | Normalises rating mentions. | Adjust thresholds or add language variants; rerun unit tests in `tests/test_review_advanced.py`. |
| Whitelist | `dictionary/whitelist.json` | Tokens protected across pipeline steps. | Add placeholders if you introduce new masking tokens. |

Place patches under `data/processed/` or a similar directory if you prefer not to edit vendored files; then override loaders in your application before invoking Leksara.

---

## Interoperability tips

- **Pandas pipelines** – Apply `leksara(...)` to Series directly to avoid intermediate Python loops; the library handles non-string values by returning them unchanged so mixed dtype Series are safe.
- **Spark / Dask** – Wrap `ReviewChain.process_text` inside UDFs for distributed processing. Cache resource loaders to prevent repeated JSON parsing on workers.
- **Airflow / Prefect** – Emit benchmark metrics as task logs or push them to monitoring systems to track pipeline health.
- **Evaluation workflows** – Use `CartBoard` before and after cleaning to verify that PII flags drop to `False`; persist comparisons for audit trails.

For more practical scenarios, copy the recipes in `docs/examples.md` and adapt them to your orchestrator or runtime environment.


