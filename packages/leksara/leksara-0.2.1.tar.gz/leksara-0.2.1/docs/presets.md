# Preset Catalogue

Presets bundle pattern detectors and cleaning functions that work well together for common Indonesian review scenarios. They are defined in `leksara/core/presets.py` and can be consumed through either the functional API or `ReviewChain`.

---

## Available presets

| Name | Description | Included pattern detectors | Included functions | Optional dependencies |
| --- | --- | --- | --- | --- |
| `ecommerce_review` | General-purpose cleaning for marketplace reviews and chat transcripts. Focuses on PII masking, casing, token normalisation, and punctuation cleanup. | `replace_id`, `replace_phone`, `replace_email`, `replace_address` (all invoked with `mode="replace"`). | `remove_tags`, `case_normal`, `replace_url(mode="remove")`, `remove_emoji(mode="replace")`, `replace_rating`, `expand_contraction`, `normalize_slangs(mode="replace")`, `replace_acronym(mode="replace")`, `word_normalization`, `remove_stopwords`, `shorten_elongation`, `remove_punctuation`, `remove_whitespace`. | `emoji` (for richer emoji mapping), `Sastrawi` (for `word_normalization`). |

> **Note**: `word_normalization` automatically falls back to returning the original text when `Sastrawi` is missing, so the preset still works in lightweight environments.

---

## Loading presets

```python
from leksara.core.presets import get_preset
from leksara import leksara

clean = leksara([
    "Produk mantap! Email saya user@example.com. Rating 5/5",
], preset="ecommerce_review")

print(clean)
```

- `get_preset(name)` returns the raw dictionary (`{"patterns": [...], "functions": [...]}`), which you can pass directly to `ReviewChain.from_steps(**preset)` if you need an object-oriented orchestrator.
- `leksara(..., preset="ecommerce_review")` is a shorthand that pulls the same definition internally.

---

## Extending a preset

```python
from leksara import leksara
from leksara.core.presets import get_preset
from leksara.function import remove_digits
from leksara.pattern import replace_address

preset = get_preset("ecommerce_review")
preset["patterns"].append((replace_address, {"mode": "replace", "street": True}))
preset["functions"].insert(0, remove_digits)

texts = ["Alamat: Jl. Melati 12, rating 4/5"]
print(leksara(texts, pipeline=preset))
```

- Mutating the list is safe as long as you are working on a copy returned by `get_preset`. Each call returns a new dictionary, so global state is not affected.
- Use `insert` to control execution order; new functions run in the order they appear.

---

## Authoring your own preset

1. Decide which PII patterns must run before general cleaning (phones, emails, NIK, addresses). Import them from `leksara.pattern`.
2. Pick cleaning primitives in the order recommended by `features.md` (case normalisation → URL/emoji replacement → stopwords → punctuation → whitespace).
3. Inline advanced steps such as `replace_rating` or `normalize_slangs` when the use case demands them.
4. Return the configuration as a dictionary and register it in `PRESETS` inside `core/presets.py`.

```python
def support_ticket() -> dict:
    return {
        "patterns": [
            (replace_phone, {"mode": "replace"}),
            (replace_email, {"mode": "replace"}),
        ],
        "functions": [
            case_normal,
            replace_url,
            remove_stopwords,
            remove_punctuation,
            remove_whitespace,
        ],
    }
```

> After adding a new preset, update the table above and create targeted tests under `tests/test_chain.py` or a new test module to ensure the preset behaves as expected.

---

## Troubleshooting presets

- **`ValueError: Preset '<name>' tidak ditemukan.`** – Ensure the preset is declared in the `PRESETS` mapping and exported via `__all__` if you want top-level imports.
- **Masking order issues** – Pattern detectors run in the order listed. Place `replace_phone` before `replace_address` to avoid double masking overlapping tokens.
- **Optional dependency missing** – Install the extra listed in the table or remove the function from the preset.
- **Benchmark drift** – Use `leksara(..., benchmark=True)` each time you tweak preset definitions to confirm latency remains acceptable.
