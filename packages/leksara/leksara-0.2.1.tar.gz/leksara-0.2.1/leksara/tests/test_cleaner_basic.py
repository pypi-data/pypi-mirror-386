import pytest

from leksara.functions.cleaner.basic import (
    remove_tags,
    case_normal,
    remove_stopwords,
    remove_whitespace,
    remove_digits,
    remove_punctuation,
    replace_url,
    remove_emoji,
)


def test_remove_tags_and_entities():
    text = "<p>Halo &amp; selamat\u00A0datang</p>"
    out = remove_tags(text)
    assert out == "Halo & selamat datang"

    # non-str should return as is
    assert remove_tags(123) == 123


def test_case_normal():
    assert case_normal("Produk BAGUS!!!") == "produk bagus!!!"
    # non-str passthrough
    obj = {"a": 1}
    assert case_normal(obj) is obj


def test_remove_stopwords():
    text = "produk ini bagus dan cepat"
    out = remove_stopwords(text)
    # should remove common Indonesian stopwords like 'ini' and 'dan'
    assert "ini" not in out
    assert "dan" not in out

    # non-str passthrough
    assert remove_stopwords(None) is None


def test_remove_whitespace():
    assert remove_whitespace("  a   b\n\t c  ") == "a b c"
    # non-str passthrough
    assert remove_whitespace(0) == 0


def test_remove_digits():
    assert remove_digits("abc123def45") == "abcdef"
    with pytest.raises(TypeError):
        remove_digits(None)


def test_remove_punctuation_basic():
    text = "halo!!! keren—bagus…"
    out = remove_punctuation(text)
    assert out == "halo kerenbagus"


def test_remove_punctuation_with_exclude():
    text = "halo!?"
    out = remove_punctuation(text, exclude="?")
    assert out == "halo?"
    with pytest.raises(TypeError):
        remove_punctuation("halo", exclude=123)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        remove_punctuation(None)  # type: ignore[arg-type]


def test_replace_url_remove_and_replace():
    text = "Kunjungi https://shop.id/path?x=1 dan juga www.toko.co.id/page"
    out_remove = replace_url(text, mode="remove")
    assert "http" not in out_remove and "www." not in out_remove

    out_replace = replace_url(text, mode="replace")
    assert "[URL]" in out_replace

    with pytest.raises(TypeError):
        replace_url(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        replace_url(text, mode="keep")  # invalid mode


def test_remove_emoji_remove_and_replace():
    text = "Mantap 👍😂"
    out_remove = remove_emoji(text, mode="remove")
    assert "👍" not in out_remove and "😂" not in out_remove

    out_replace = remove_emoji(text, mode="replace")
    # replacement inserts mapping words; ensure known keywords appear
    assert "bagus" in out_replace  # from 👍 mapping
    assert "ketawa" in out_replace  # from 😂 mapping phrase

    with pytest.raises(TypeError):
        remove_emoji(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        remove_emoji(text, mode="unknown")
