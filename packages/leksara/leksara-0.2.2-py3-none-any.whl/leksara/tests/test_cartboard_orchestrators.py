import pandas as pd
import pytest

from leksara.frames.cartboard import CartBoard, get_flags, get_stats, noise_detect


def test_get_flags_dataframe_matches_spec():
    df = pd.DataFrame(
        {
            "review_id": [1, 2, 3],
            "review_text": [
                "<p>bagus jg kualitasnya, 5/5⭐️ deh</p>",
                "barang ok, hubungi 081234567890 ya",
                "good quality, pengiriman cepat bgt",
            ],
        }
    )

    result = get_flags(df, text_column="review_text")

    assert list(result.columns) == [
        "review_id",
        "review_text",
        "rating_flag",
        "pii_flag",
        "non_alphabetical_flag",
    ]

    row1, row2 = result.iloc[0], result.iloc[1]

    assert bool(row1["rating_flag"])
    assert not bool(row1["pii_flag"])
    assert bool(row1["non_alphabetical_flag"])

    assert bool(row2["pii_flag"])
    assert not bool(row2["non_alphabetical_flag"])


def test_get_flags_series_without_merge_returns_original():
    series = pd.Series([
        "Ini dan the best service, email saya user@example.com!!!",
    ])

    result = get_flags(series, merge_input=False)
    row = result.iloc[0]

    assert bool(row["pii_flag"])
    assert bool(row["non_alphabetical_flag"])
    assert row["original_text"].startswith("Ini dan the best service")


def test_get_stats_and_noise_detect_dict_outputs():
    text = (
        "<p>Promo besar 50% di https://shop.id 😀</p> "
        "Hubungi 0812-3456-7890 atau +62 812 3456 7890 "
        "Email: support+promo@lige-official.co.id"
    )
    df = pd.DataFrame({"review_id": [42], "review_text": [text]})

    stats = get_stats(df, text_column="review_text")
    noise = noise_detect(df, text_column="review_text")

    stats_payload = stats.iloc[0]["stats"]
    noise_payload = noise.iloc[0]["detect_noise"]

    assert stats_payload["emojis"] >= 1
    assert stats_payload["noise_count"] >= 1
    assert any(url.startswith("http") for url in noise_payload["urls"])
    assert any(tag.startswith("<p") for tag in noise_payload["html_tags"])
    assert any("@" in email for email in noise_payload["emails"])
    assert "0812-3456-7890" in noise_payload["phones"]
    assert "+62 812 3456 7890" in noise_payload["phones"]
    assert noise_payload["phones_normalized"][0].startswith("0812")

def test_get_flags_from_string_input_without_merge():
    result = get_flags("Rating 4/5 mantap banget!", merge_input=False)
    assert set(result.columns) == {
        "original_text",
        "rating_flag",
        "pii_flag",
        "non_alphabetical_flag",
    }
    row = result.iloc[0]
    assert row["original_text"] == "Rating 4/5 mantap banget!"
    assert bool(row["rating_flag"]) is True


def test_noise_detect_without_merge_excludes_normalized_when_requested():
    noise = noise_detect(["Hubungi 081234567890"], merge_input=False, include_normalized=False)
    payload = noise.iloc[0]["detect_noise"]
    assert "phones" in payload and payload["phones"]
    assert "phones_normalized" not in payload


def test_cartboard_flags_and_metadata():
    text = "Email saya user@example.com, rating 5/5!"
    board = CartBoard(text, rating=4.5)
    data = board.to_dict()
    assert data["rating"] == 4.5
    assert data["pii_flag"] is True
    assert "refined_text" not in data


def test_cartboard_requires_string_input():
    with pytest.raises(TypeError):
        CartBoard(123)  # type: ignore[arg-type]
