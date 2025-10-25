# API Reference

This document lists the public interfaces exposed by Leksara. Use it as a quick lookup for function signatures, parameter behaviour, and return payloads. Deeper explanations, design rationales, and usage tips live in `docs/features.md` and `docs/examples.md`.

---

## Table of Contents

1. [Functional pipeline (`leksara`)](#functional-pipeline-leksara)
2. [ReviewChain class](#reviewchain-class)
3. [CartBoard & frame utilities](#cartboard--frame-utilities)
4. [Cleaning primitives (`leksara.function`)](#cleaning-primitives-leksarafunction)
5. [PII utilities (`leksara.pattern`)](#pii-utilities-leksarapattern)
6. [Review normalisation utilities](#review-normalisation-utilities)
7. [Logging helpers](#logging-helpers)
8. [Preset management](#preset-management)

---

## Functional pipeline (`leksara`)

```python
from leksara import leksara
```

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| `data` | Iterable of `str` or `pandas.Series` | Texts to transform. Non-string entries are forwarded unchanged. | ✅ |
| `pipeline` | `dict` or `None` | Custom pipeline definition with keys `"patterns"` and `"functions"`. Each value is a list of callables or `(callable, kwargs)` tuples. | ❌ (mutually exclusive with `preset` unless you intentionally override steps) |
| `preset` | `str` or `None` | Name of preset defined in `leksara.core.presets`. Ignored when `pipeline` is supplied. | ❌ |
| `benchmark` | `bool` | When `True`, return timing metadata alongside results. | ❌ |

### Returns

- When `benchmark=False`: cleaned data (list when input iterable, `Series` when input Series).
- When `benchmark=True`: tuple `(cleaned, metrics)` where `metrics` is a dict containing `n_steps`, `total_time_sec`, and `per_step` timing entries.

### Exceptions

- `ValueError` when both `pipeline` and `preset` are provided and conflict.
- `TypeError` if pipeline definitions are not callables / `(callable, dict)` tuples.

---

## ReviewChain class

```python
from leksara.core.chain import ReviewChain
```

### Constructors

| Method | Description |
| --- | --- |
| `ReviewChain.from_steps(*, patterns=None, functions=None)` | Build a chain from explicit step lists. Accepts `None`, callable, or `(callable, kwargs)` entries. |
| `ReviewChain.from_preset(name: str)` | Load a preset from `leksara.core.presets`. |

### Runtime methods

| Method | Signature | Behaviour |
| --- | --- | --- |
| `process_text(text)` | `str -> str` | Run the configured pipeline on a single string. Non-string values raise `TypeError`. |
| `transform(data, *, benchmark=False)` | `Iterable[str]` or `pandas.Series` | Returns cleaned data (same type as input). When `benchmark=True`, returns `(data, metrics)`. |
| `run_on_series(series, *, benchmark=False)` | `pandas.Series` | Identical to `transform` but keeps Series metadata (index, name). |
| `named_steps` | Property | Ordered mapping of step names to callables for debugging or inspection. |

### Benchmark schema

Both `.transform(..., benchmark=True)` and `leksara(..., benchmark=True)` emit:

```python
{
  "n_steps": int,
  "total_time_sec": float,
  "per_step": List[Tuple[str, float]],
}
```

---

## CartBoard & frame utilities

```python
from leksara.frames.cartboard import CartBoard, get_flags, get_stats, noise_detect
```

| API | Parameters | Returns | Notes |
| --- | --- | --- | --- |
| `CartBoard(raw_text: str, rating: float \| int \| None = None)` | `raw_text`: required string. `rating`: optional numeric score. | Dataclass-like object with properties `.original_text`, `.rating`, `.pii_flag`, `.non_alphabetical_flag`. | Call `.to_dict()` to serialise. |
| `get_flags(data, *, text_column="text", non_alpha_threshold=0.15, merge_input=True)` | `data`: str/list/Series/DataFrame. `text_column`: source column inside DataFrame/Series. | `pandas.DataFrame` containing flag columns (`rating_flag`, `pii_flag`, `non_alphabetical_flag`) plus original data when `merge_input=True`. | Uses regex + heuristics to determine noise. |
| `get_stats(data, *, text_column="text", merge_input=True, as_dict=True)` | Same data handling as `get_flags`. `as_dict=True` nests stats per row. | Frame with `stats` payload (length, word_count, Indonesian stopword hits, emojis, whitespace ratios). | Set `as_dict=False` to expand stats into top-level columns. |
| `noise_detect(data, *, text_column="text", merge_input=True, include_normalized=True)` | Controls whether normalized phone numbers are included. | Frame with `detect_noise` dictionary: `urls`, `html_tags`, `emails`, `phones`, `phones_normalized`, `emojis`. | Useful for audits and dashboards. |

---

## Cleaning primitives (`leksara.function`)

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

| Function | Signature | Summary |
| --- | --- | --- |
| `remove_tags(text)` | `str -> str` | Removes HTML/XML tags using regex patterns. |
| `case_normal(text)` | `str -> str` | Lowercases text and standardises unicode punctuation. |
| `remove_stopwords(text, stopwords=None)` | `str -> str` | Removes Indonesian stopwords. `stopwords` accepts iterable overrides (merged with defaults). |
| `remove_whitespace(text)` | `str -> str` | Collapses multiple spaces/tabs/newlines, trims ends. |
| `remove_punctuation(text)` | `str -> str` | Removes punctuation characters while preserving placeholder brackets. |
| `remove_digits(text)` | `str -> str` | Drops ASCII digits. |
| `remove_emoji(text)` | `str -> str` | Removes emoji code points. Falls back to identity when `emoji` package is missing. |
| `replace_url(text, mode="remove"\|"replace", placeholder="[URL]")` | `str -> str` | Detects URLs (with optional protocol) and either removes or replaces them with the placeholder. |

All helpers return the original value when given `None`, non-string objects, or empty strings. Downstream pipelines rely on this behaviour to gracefully handle `NaN` in Series.

---

## PII utilities (`leksara.pattern`)

```python
from leksara.pattern import (
  replace_phone,
  replace_address,
  replace_email,
  replace_id,
)
```

| Function | Required args | Optional args | Behaviour |
| --- | --- | --- | --- |
| `replace_phone(text, mode="remove"\|"replace")` | `text` | `mode`, `placeholder` (defaults to `[PHONE_NUMBER]`) | Detects Indonesian phone numbers (`+62`, `62`, `0` prefixes, spacing/dash variations). Returns original text if number appears invalid. |
| `replace_email(text, mode="remove"\|"replace")` | `text` | `mode`, `placeholder` (`[EMAIL]`) | Case-insensitive email masking; supports plus addressing. |
| `replace_address(text, mode="remove"\|"replace", **components)` | `text` | Component toggles such as `street`, `city`, `rtrw`, `postal_code`. Placeholder default `[ADDRESS]`. | Uses trigger phrases and component-level regex windows. Unknown component keywords raise `KeyError`. |
| `replace_id(text, mode="remove"\|"replace")` | `text` | Placeholder `[NIK]`. | Detects 16-digit NIK patterns. |

All functions raise `TypeError` when `text` is not a string to enforce explicit handling upstream.

---

## Review normalisation utilities

```python
from leksara.function import (
  replace_rating,
  shorten_elongation,
  replace_acronym,
  normalize_slangs,
  expand_contraction,
  word_normalization,
)
```

| Function | Key parameters | Result |
| --- | --- | --- |
| `replace_rating(text, placeholder="__RATING__", normalize_scale=True)` | `placeholder`: custom token. `normalize_scale`: map arbitrary x/10 scales to 0–5 range. `blacklist`: optional iterable of substrings to ignore. | Returns text with rating mentions replaced by numeric string or placeholder. |
| `shorten_elongation(text, max_repeat=2)` | `max_repeat` must be ≥1. | Reduces consecutive repeated characters beyond threshold. |
| `replace_acronym(text, mode="replace"\|"remove")` | Uses acronym dictionary and conflict rules. | Replaces or removes acronyms; context-sensitive for ambiguous tokens. |
| `normalize_slangs(text, mode="replace"\|"remove")` | `mode`. | Substitutes colloquial slang with dictionary entries. |
| `expand_contraction(text)` | – | Expands Indonesian contractions; returns original value when not a string. |
| `word_normalization(text, method="stem", word_list=None, mode="keep")` | `method`: currently `"stem"`. `word_list`: iterable of tokens to protect or include depending on `mode`. `mode`: `keep`, `only`, `exclude`. | Applies stemming using Sastrawi when available; automatically masks placeholders before stemming. |

---

## Logging helpers

```python
from leksara.core.logging import setup_logging, log_pipeline_step
```

| Function | Signature | Purpose |
| --- | --- | --- |
| `setup_logging(*, log_file="pipeline.log", level="INFO")` | Configures a root logger with console + file handlers. | Call once at application start to collect pipeline diagnostics. |
| `log_pipeline_step(pipeline_name, raw_text, processed_text, *, extra=None)` | Appends a structured log entry capturing before/after text. | Use in compliance-sensitive environments to audit redaction. |

Both functions respect Python’s standard logging configuration and can be integrated with custom handlers.

---

## Preset management

```python
from leksara.core.presets import get_preset, list_presets
```

| Function | Description |
| --- | --- |
| `list_presets()` | Returns an iterable of available preset names bundled with the package. |
| `get_preset(name)` | Retrieves a preset definition dict containing `"patterns"` and `"functions"`. Raises `KeyError` for unknown names. |

Preset dictionaries can be modified before passing to `leksara(...)` or `ReviewChain.from_steps` to add/remove stages.
