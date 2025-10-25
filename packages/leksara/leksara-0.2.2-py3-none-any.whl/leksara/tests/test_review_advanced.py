import re
import pytest

import leksara.functions.review.advanced as adv  # untuk monkeypatching
from leksara.functions.review.advanced import (
    expand_contraction,
    normalize_slangs,
    replace_acronym,
    replace_rating,
    shorten_elongation,
    word_normalization,
    mask_rating_tokens,
    unmask_rating_tokens,
)
from leksara.functions.cleaner.basic import remove_punctuation

RATING_PLACEHOLDER = "__RATING_"

@pytest.mark.parametrize("text, expected", [
    ("Hallooooo teman-temannn", "Halloo teman-temann"),
    ("Kerennnn bangettsss", "Kerenn bangettss"),
    ("Waahhh mantap jiwaaa", "Waahh mantap jiwaa"),
    ("Ini teks normal", "Ini teks normal"),
    ("Bagus", "Bagus"),
    ("aaaaa", "aa"),
    ("", ""),
])
    
def test_shorten_elongation_reduces_repeats_with_default_max(text, expected):
    assert shorten_elongation(text) == expected

@pytest.mark.parametrize("text, max_repeat, expected", [
    ("Mantuuulll", 1, "Mantul"),
    ("Gilaaa benarrr", 1, "Gila benar"),
    ("Tanggapan", 1, "Tangapan"),
    ("Wooooowwwww", 3, "Wooowww"),
    ("Kereeeen", 4, "Kereeeen"), 
])
def test_shorten_elongation_with_custom_max_repeat(text, max_repeat, expected):
    assert shorten_elongation(text, max_repeat=max_repeat) == expected

@pytest.mark.parametrize("invalid_max", [0, -1, -100])
def test_shorten_elongation_invalid_max_repeat_raises_value_error(invalid_max):
    with pytest.raises(ValueError, match="max_repeat must be >= 1"):
        shorten_elongation("tes", max_repeat=invalid_max)


def test_shorten_elongation_type_error_on_non_string():
    with pytest.raises(TypeError):
        shorten_elongation(12345)


@pytest.mark.parametrize(
    "text, expected",
    [
    ("Rating: 4,5/5 mantap", "Rating: 4.5 mantap"),
    ("Score: 8/10", "Score: 4.0"),
    ("kasih lima bintang", "kasih 5.0"),
    ("4 of 5 for design", "4.0 for design"),
    ("rating: 5", "5.0"),
    ("3 stars overall", "3.0 overall"),
    ("Kualitasnya ⭐⭐⭐⭐ top!", "Kualitasnya 4.0 top!"),
    ("Keren banget ⭐ x5, mantap!", "Keren banget 5.0, mantap!"),
    ],
)
def test_replace_rating_positive_cases(text, expected):
    out = replace_rating(text)
    assert out == expected


def test_replace_rating_out_of_5_any():
    text = "Rating: 4,5/5 mantap"
    out = replace_rating(text)
    assert re.search(r"\d+(\.\d+)?", out)
    assert "4.5" in out or RATING_PLACEHOLDER in out


def test_replace_rating_out_of_any_scale_normalizes():
    text = "Score: 8/10"
    out = replace_rating(text)
    rating_val = float(re.findall(r"\d+(\.\d+)?", out)[0])
    assert 0 <= rating_val <= 5


def test_replace_rating_bintang_any_with_word_map():
    text = "kasih lima bintang"
    out = replace_rating(text)
    assert re.search(r"\d+(\.\d+)?", out)
    assert "5" in out or RATING_PLACEHOLDER in out


def test_replace_rating_number_of_five():
    text = "4 of 5 for design"
    out = replace_rating(text)
    assert "4.0" in out and "of 5" not in out


def test_replace_rating_rating_word_number():
    text = "rating: 5"
    out = replace_rating(text)
    assert "5" in out or RATING_PLACEHOLDER in out


def test_replace_rating_stars_word_any():
    text = "3 stars overall"
    out = replace_rating(text)
    assert "3.0" in out and " stars" not in out


def test_replace_rating_emoji_stars_sequence():
    text = "Kualitasnya ⭐⭐⭐⭐ top!"
    out = replace_rating(text)
    assert "4.0" in out and "⭐⭐⭐⭐" not in out


def test_replace_rating_emoji_stars_multiplied():
    text = "Keren banget ⭐ x5, mantap!"
    out = replace_rating(text)
    assert "5.0" in out and "⭐ x5"


def test_replace_rating_blacklist_ignored():
    text = "★"
    out = replace_rating(text)
    assert "★" in out


def test_replace_rating_multiple_ratings_in_text():
    text = "Film A: 4/5, Film B: 3/5"
    out = replace_rating(text)
    placeholders_count = len(re.findall(RATING_PLACEHOLDER, out))
    assert placeholders_count >= 2 or re.findall(r"\d+(\.\d+)?", out)


def test_replace_rating_type_error_on_non_string():
    with pytest.raises(TypeError):
        replace_rating(12345)


def test_replace_rating_returns_original_if_no_pattern_found():
    text = "Tidak ada rating di sini"
    out = replace_rating(text)
    assert out == text


def test_replace_rating_collapses_whitespace_after_replacement():
    text = "Rating:  4  /5   sangat bagus"
    out = replace_rating(text)
    assert "  " not in out


def test_mask_unmask_rating_tokens_survive_punctuation_removal():
    text = "rating 4.5"
    masked = mask_rating_tokens(replace_rating(text))
    assert masked != replace_rating(text)
    assert "4.5" not in masked
    # remove_punctuation menghapus titik, sentinel harus menjaga format
    stripped = remove_punctuation(masked)
    restored = unmask_rating_tokens(stripped)
    assert "4.5" in restored


@pytest.fixture
def slang_env(monkeypatch):
    monkeypatch.setattr(
        adv,
        "_SLANGS_DICT",
        {
            "brb": "be right back",
            "gw": "gue",
            "keren": "bagus",
            "sip": "oke",
            "kw": ["keren", "bagus"],
        },
        raising=False,
    )
    monkeypatch.setattr(adv, "_CONFLICT_RULES", {}, raising=False)
    return adv, monkeypatch


@pytest.fixture
def acronym_env(monkeypatch):
    monkeypatch.setattr(
        adv,
        "_ACRONYM_DICT",
        {
            "hp": "handphone",
            "m": ["meter", "medium"],
        },
        raising=False,
    )
    monkeypatch.setattr(
        adv,
        "_CONFLICT_RULES",
        {
            "m": {
                "rules": [
                    {"context_pattern": r"(\d+)\s*m\b", "preferred": "meter"},
                    {"context_pattern": r"\bsize\s*m\b", "preferred": "medium"},
                ]
            }
        },
        raising=False,
    )
    return adv


@pytest.fixture
def contraction_env(monkeypatch):
    monkeypatch.setattr(
        adv,
        "_CONTRACTIONS_DICT",
        {
            "gk": "tidak",
            "yg": "yang",
        },
        raising=False,
    )
    return adv

def test_replace_basic(slang_env):
    out = normalize_slangs("brb nanti ya")
    assert "be right back" in out
    assert "brb" not in out.lower()

def test_remove_mode_removes_tokens(slang_env):
    out = normalize_slangs("gw, nanti ya", mode="remove")
    assert "gw" not in out.lower()
    assert "nanti" in out

def test_case_insensitive_and_punctuation(slang_env):
    out = normalize_slangs("BRB!!!")
    assert "be right back" in out

def test_multiple_occurrences_and_boundaries(slang_env):
    s = "brb, brb. brb? gw brb"
    out = normalize_slangs(s)
    assert out.lower().count("be right back") == 4
    assert "gue" in out

def test_list_value_uses_first_item(slang_env):
    out = normalize_slangs("kw banget")
    assert "keren" in out
    assert "bagus" not in out

def test_conflict_rule_applies_preferred(slang_env):
    _, mp = slang_env
    mp.setattr(adv, "_SLANGS_DICT", {"gw": "gue"}, raising=False)

    fake_conflict = {
        "gw": {
            "rules": [
                {
                    "context_pattern": r"\baku\b",
                    "preferred": "saya"
                }
            ]
        }
    }
    mp.setattr(adv, "_CONFLICT_RULES", fake_conflict, raising=False)

    text1 = "gw aku nanti"
    out1 = normalize_slangs(text1)
    assert "saya" in out1

    text2 = "gw dia saja"
    out2 = normalize_slangs(text2)
    assert re.search(r"\bgw\b", out2, re.IGNORECASE)

def test_empty_slangs_returns_original(monkeypatch):
    monkeypatch.setattr(adv, "_SLANGS_DICT", {}, raising=False)
    txt = "brb gw keren"
    out = normalize_slangs(txt)
    assert out == txt

def test_non_string_raises_typeerror():
    with pytest.raises(TypeError):
        normalize_slangs(123)

def test_invalid_mode_raises_valueerror():
    with pytest.raises(ValueError):
        normalize_slangs("brb", mode="delete")


def test_replace_acronym_replace_mode(acronym_env):
    out = replace_acronym("HP ini bagus", mode="replace")
    assert "handphone" in out


def test_replace_acronym_remove_mode(acronym_env):
    out = replace_acronym("HP ready stock", mode="remove")
    assert "hp" not in out.lower()
    assert "ready stock" in out


def test_replace_acronym_conflict_rules_select_proper_expansion(acronym_env):
    measurement = replace_acronym("Panjang 10 m", mode="replace")
    assert "meter" in measurement

    sizing = replace_acronym("size m pas", mode="replace")
    assert "medium" in sizing


def test_replace_acronym_invalid_mode_raises_valueerror(acronym_env):
    with pytest.raises(ValueError):
        replace_acronym("HP", mode="mask")


def test_replace_acronym_type_error():
    with pytest.raises(TypeError):
        replace_acronym(123)  # type: ignore[arg-type]


def test_word_normalization_basic_stem():
    text = "Saya sedang bermain bola"
    out = word_normalization(text)
    assert "main" in out
    assert "bermain" not in out


def test_word_normalization_whitelist_keep():
    text = "Saya sedang bermain bola"
    word_list = ["bermain"]
    out = word_normalization(text, word_list=word_list, mode="keep")
    assert re.search(r"\bbermain\b", out)
    assert not re.search(r"\bmain\b", out)


def test_word_normalization_whitelist_only():
    text = "Saya sedang bermain bola"
    word_list = ["bermain"]
    out = word_normalization(text, word_list=word_list, mode="only")
    assert "main" in out
    assert "bermain" not in out


def test_word_normalization_protect_bracket():
    text = "Ini adalah dan [PHONE_NUMBER]"
    out = word_normalization(text)
    assert "[PHONE_NUMBER]" in out


def test_word_normalization_empty_string():
    assert word_normalization("") == ""


def test_word_normalization_non_string_input():
    assert word_normalization(12345) == 12345
    assert word_normalization(None) is None


def test_word_normalization_mode_invalid_raises_value_error():
    with pytest.raises(ValueError):
        word_normalization("test", mode="invalid")

def test_expand_contraction_replaces_tokens(contraction_env):
    out = expand_contraction("gk mau yg lain")
    assert "tidak mau yang" in out


def test_expand_contraction_preserves_uppercase(contraction_env):
    out = expand_contraction("YG BAGUS")
    assert out == "YANG BAGUS"


def test_expand_contraction_non_string_returns_original(contraction_env):
    assert expand_contraction(123) == 123


def test_expand_contraction_returns_original_when_dictionary_missing(monkeypatch):
    monkeypatch.setattr(adv, "_CONTRACTIONS_DICT", {}, raising=False)
    text = "gk mau"
    assert expand_contraction(text) == text
