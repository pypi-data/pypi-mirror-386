from leksara.functions.patterns.pii import replace_phone, replace_email, replace_address, replace_id
from leksara.functions.cleaner.basic import remove_digits, remove_emoji, remove_tags, case_normal, remove_whitespace, remove_punctuation, remove_stopwords, replace_url
from leksara.functions.review.advanced import shorten_elongation, word_normalization, replace_rating, expand_contraction, normalize_slangs, replace_acronym

def ecommerce_review():
    return {
        "patterns": [
            (replace_phone, {"mode": "replace"}),
            (replace_email, {"mode": "replace"}),
            (replace_address, {"mode": "replace"}),
            (replace_id, {"mode": "replace"}),
        ],
        "functions": [
            remove_tags,
            case_normal,
            (replace_url, {"mode": "replace"}),
            (remove_emoji, {"mode": "replace"}),
            # replace_rating,
            # expand_contraction,
            # normalize_slangs,
            # replace_acronym,
            word_normalization, 
            remove_stopwords,
            shorten_elongation,
            remove_punctuation,
            remove_whitespace,
        ],
    }

PRESETS = {
    "ecommerce_review": ecommerce_review
}

def get_preset(name: str):
    if name not in PRESETS:
        raise ValueError(f"Preset '{name}' tidak ditemukan.")
    return PRESETS[name]()
