# Usage Guide

This page demonstrates common workflows for using Leksara in notebooks, batch jobs, and streaming services. Combine these snippets with the conceptual explanations in `features.md` and the recipes in `examples.md`.

---

## Clean reviews with the functional API

```python
import pandas as pd
from leksara import leksara

reviews = pd.Series(
    [
        "Barangnya baaaagus banget!!! COD lancar, cs ramah. Email: cs@shop.id",
        "Pengiriman lambat :( tolong hubungi +62 812-3333-4444",
    ]
)

cleaned, metrics = leksara(reviews, preset="ecommerce_review", benchmark=True)

print(cleaned.head())
print(metrics)
```

- The return type matches the input (`Series` in, `Series` out).
- `benchmark=True` is optional but recommended when profiling new resources or large batches.
- You can pass `pipeline=` instead of `preset=` when you want full control over the steps (see below).

---

## Build a custom pipeline

```python
from leksara import leksara
from leksara.function import case_normal, remove_stopwords, remove_punctuation
from leksara.pattern import replace_phone, replace_email

custom_pipeline = {
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

texts = ["Hubungi kami di 0812-3456-7890 atau support@shop.id"]
print(leksara(texts, pipeline=custom_pipeline))
```

- Tuples of `(callable, kwargs)` let you fine-tune each step without mutating global state.
- Any non-string items in `texts` are returned unchanged; handle them upstream if you need stricter validation.

---

## Reuse pipelines with `ReviewChain`

```python
from leksara import ReviewChain
from leksara.core.presets import get_preset

chain = ReviewChain.from_steps(**get_preset("ecommerce_review"))

payload = {"id": "rev-01", "message": "Rating 5/5! Email saya user@shop.id"}

processed, timings = chain.transform([payload["message"]], benchmark=True)
payload["clean_message"] = processed[0]
payload["timings"] = timings

print(payload)
```

- Instantiate the chain once and reuse it across events to avoid repeated dictionary loads.
- `.process_text` is ideal when you only have single strings but still want the same benchmark schema.

---

## Audit text before and after cleaning

```python
import pandas as pd
from leksara.frames.cartboard import get_flags, get_stats, noise_detect

raw = pd.Series([
    "Barangnya mantap!!! Email saya user@example.com",
    "<p>Promo 50% di https://shop.id 😀</p> Hubungi 0812 1234 5678",
])

flags = get_flags(raw)
stats = get_stats(raw)
noise = noise_detect(raw, include_normalized=False)

print(flags[["pii_flag", "non_alphabetical_flag"]])
print(stats.iloc[0]["stats"])
print(noise.iloc[1]["detect_noise"])
```

- CartBoard utilities do not mutate text and therefore make excellent pre-flight and post-cleaning validation tools.
- Disable `include_normalized` when you only want artefacts as they originally appeared.

---

## Update dictionaries at runtime

```python
from pathlib import Path
import json

import leksara.functions.review.advanced as adv

slang_path = Path(adv.__file__).resolve().parent.parent / "resources" / "dictionary" / "slangs_dict.json"
data = json.loads(slang_path.read_text(encoding="utf-8"))
data.update({"wfh": "bekerja dari rumah"})
adv._SLANGS_DICT = data  # applies for the current process
```

- Many advanced utilities cache dictionaries on import. Modify the cache before running pipelines to experiment quickly.
- Restart your process (or reload the module) to discard temporary overrides.

---

## Common defaults & policies

- Import PII masking helpers from `leksara.pattern` and cleaning helpers from `leksara.function` to keep dependencies explicit.
- Placeholder tokens such as `[PHONE_NUMBER]` and `[EMAIL]` are preserved by cleaning functions to avoid double masking.
- `word_normalization` returns input text unchanged when `Sastrawi` is not present. Install the optional dependency or guard the step.
- Pattern detectors raise `TypeError` when they receive non-string inputs; wrap your loaders with `.fillna("")` or filter out invalid entries if this is undesirable.

---

## Related reading

- `features.md` – Strategic guidance for each feature and best practices for ordering steps.
- `examples.md` – End-to-end scenarios including streaming pipelines and preset customisation.
- `benchmarks.md` – How to capture and persist timing metrics.

