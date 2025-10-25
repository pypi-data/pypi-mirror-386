# Examples and Recipes

These walkthroughs show the raw data you feed into Leksara, the exact code you run, and the transformed outputs in table form. Each scenario keeps the library’s execution order intact: PII masking first, then cleaning functions.

---

## 1. CartBoard Audit Walkthrough

### 1.1 CartBoard Input Records

| review_id | channel   | text                                                                          |
|-----------|-----------|--------------------------------------------------------------------------------|
| 21        | Tokopedia | Produk kece bgt!!! Email saya `user@mail.id` ⭐⭐⭐⭐⭐                            |
| 22        | Shopee    | Pengiriman lambat :( Hubungi 0812-3456-7890                                   |
| 23        | Lazada    | Oke lah, cuma packing agak rusak                                               |

### 1.2 CartBoard Python Code

```python
import pandas as pd
from leksara.frames.cartboard import get_flags, get_stats, noise_detect

reviews = pd.DataFrame(
    {
        "review_id": [21, 22, 23],
        "channel": ["Tokopedia", "Shopee", "Lazada"],
        "text": [
            "Produk kece bgt!!! Email saya user@mail.id ⭐⭐⭐⭐⭐",
            "Pengiriman lambat :( Hubungi 0812-3456-7890",
            "Oke lah, cuma packing agak rusak",
        ],
    }
)

flags = get_flags(reviews, text_column="text")
stats = get_stats(reviews, text_column="text")
noise = noise_detect(reviews, text_column="text", include_normalized=False)

flags_view = flags[["review_id", "pii_flag", "rating_flag", "non_alphabetical_flag"]]
stats_entry = stats.loc[21, "stats"]
noise_entry = noise.loc[22, "detect_noise"]

print(flags_view)
print(stats_entry)
print(noise_entry)
```

### 1.3 CartBoard Output Tables

#### 1.3.1 Flag Indicators

| review_id | pii_flag | rating_flag | non_alphabetical_flag |
|-----------|----------|-------------|------------------------|
| 21        | True     | True        | True                   |
| 22        | True     | False       | True                   |
| 23        | False    | False       | False                  |

#### 1.3.2 Stats Snapshot (review_id 21)

| metric         | value                                        |
|----------------|----------------------------------------------|
| length         | 60                                           |
| word_count     | 9                                            |
| stopwords      | 2                                            |
| punctuations   | 7                                            |
| symbols        | 0                                            |
| emojis         | 5                                            |
| noise_count    | 3                                            |
| urls           | []                                           |
| html_tags      | []                                           |
| emails         | ['user@mail.id']                             |
| phones         | []                                           |
| phones_normalized | []                                        |
| emoji_list     | ['⭐', '⭐', '⭐', '⭐', '⭐']                   |

#### 1.3.3 Noise Inspection (review_id 22)

| artifact | value               |
|----------|---------------------|
| urls     | []                  |
| html_tags| []                  |
| emails   | []                  |
| phones   | ['0812-3456-7890']  |
| phones_normalized | ['081234567890'] |
| emojis   | []                  |

CartBoard keeps the original text intact while flagging sensitive content, scores, and noise artefacts for each record.

---

## 2. Ecommerce Preset Cleanup

### 2.1 Preset Input Reviews

| idx | raw_text                                                       |
|-----|----------------------------------------------------------------|
| 0   | &lt;p&gt;MANTUL banget! ⭐⭐⭐⭐⭐ Hubungi CS: +62 812-3333-4444&lt;/p&gt;   |
| 1   | Barangnya bagus, packaging aman. Rating 4/5.                  |

### 2.2 Preset Python Code

```python
import pandas as pd
from leksara import leksara

reviews = pd.Series([
    "<p>MANTUL banget! ⭐⭐⭐⭐⭐ Hubungi CS: +62 812-3333-4444</p>",
    "Barangnya bagus, packaging aman. Rating 4/5.",
])

cleaned = leksara(reviews, preset="ecommerce_review")
print(cleaned)
```

### 2.3 Preset Output Reviews

| idx | cleaned_text                                                |
|-----|-------------------------------------------------------------|
| 0   | mantul banget __RATING_5__ hubungi cs [PHONE_NUMBER]        |
| 1   | barangnya bagus packaging aman __RATING_4__                 |

The preset automatically runs the PII masking steps (`replace_phone`, `replace_email`, `replace_address`, `replace_id`) before executing the cleaner stack (`remove_tags`, `case_normal`, `replace_url`, etc.).

---

## 3. Customize the Ecommerce Preset

### 3.1 Custom Pipeline Input Messages

| idx | raw_text                                                                    |
|-----|-----------------------------------------------------------------------------|
| 0   | Alamat lengkap: Jl. Durian No. 12 RT 01 RW 03, Jakarta. Rating: 4/5        |
| 1   | Pickup di Mall Central Park lt.3 ya                                         |

### 3.2 Custom Pipeline Python Code

```python
from leksara import leksara
from leksara.core.presets import get_preset
from leksara.function import remove_digits
from leksara.pattern import replace_address

pipeline = get_preset("ecommerce_review")
pipeline["patterns"].append((replace_address, {"mode": "replace", "street": True, "city": True}))
pipeline["functions"].append(remove_digits)

messages = [
    "Alamat lengkap: Jl. Durian No. 12 RT 01 RW 03, Jakarta. Rating: 4/5",
    "Pickup di Mall Central Park lt.3 ya",
]

print(leksara(messages, pipeline=pipeline))
```

### 3.3 Custom Pipeline Output Messages

| idx | cleaned_text                                   |
|-----|------------------------------------------------|
| 0   | alamat lengkap [ADDRESS] __RATING_4__          |
| 1   | pickup di mall central park lt ya              |

Appending `replace_address` ensures full address masking, and placing `remove_digits` at the end removes leftover numerics after masking.

---

## 4. ReviewChain for Streaming Events

### 4.1 ReviewChain Input Event

| field   | value                                                  |
|---------|--------------------------------------------------------|
| message | Halo CS, email saya `rani@shop.id`, nomor 0812333444.   |

### 4.2 ReviewChain Python Code

```python
from leksara import ReviewChain
from leksara.function import case_normal, remove_stopwords, remove_punctuation
from leksara.pattern import replace_phone, replace_email

chain = ReviewChain.from_steps(
    patterns=[
        (replace_phone, {"mode": "replace"}),
        (replace_email, {"mode": "replace"}),
    ],
    functions=[case_normal, remove_stopwords, remove_punctuation],
)

event = {"message": "Halo CS, email saya rani@shop.id, nomor 0812333444."}
cleaned, timings = chain.transform([event["message"]], benchmark=True)
print(cleaned[0])
print(timings["per_step"])
```

### 4.3 ReviewChain Output Summary

| field         | value                                              |
|---------------|----------------------------------------------------|
| cleaned_text  | halo cs email saya [EMAIL] nomor [PHONE_NUMBER]     |

#### 4.3.1 ReviewChain Per-step Timings (seconds)

| step               | seconds |
|--------------------|---------|
| replace_phone      | 0.0008  |
| replace_email      | 0.0006  |
| case_normal        | 0.0002  |
| remove_stopwords   | 0.0003  |
| remove_punctuation | 0.0001  |

Benchmarking confirms the chain executes masking steps before text normalization functions.

---

## 5. Runtime Slang Dictionary Patch

### 5.1 Slang Patch Inputs

| item             | value                                             |
|------------------|---------------------------------------------------|
| slang update map | {"bgst": "bagus", "cmiiw": "tolong koreksi jika salah"} |
| sample text      | Produk bgst banget, cmiiw tapi garansinya 2 tahun |

### 5.2 Slang Patch Python Code

```python
import json
from pathlib import Path

import leksara.functions.review.advanced as adv
from leksara.function import normalize_slangs

slang_path = Path(adv.__file__).resolve().parent.parent / "resources" / "dictionary" / "slangs_dict.json"
slang_dict = json.loads(slang_path.read_text(encoding="utf-8"))
slang_dict.update({"bgst": "bagus", "cmiiw": "tolong koreksi jika salah"})
adv._SLANGS_DICT = slang_dict

text = "Produk bgst banget, cmiiw tapi garansinya 2 tahun"
print(normalize_slangs(text))
```

### 5.3 Slang Patch Output

| field          | value                                                             |
|----------------|-------------------------------------------------------------------|
| normalized_text| Produk bagus banget, tolong koreksi jika salah tapi garansinya 2 tahun |

Advanced review helpers cache their dictionaries when imported, so patching `_SLANGS_DICT` lets you trial new terminology without editing resource files immediately.


