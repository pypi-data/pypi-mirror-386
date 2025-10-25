import re

import pandas as pd

from leksara.core.chain import ReviewChain, leksara, run_pipeline


def append_suffix(text: str, suffix: str) -> str:
    return f"{text}{suffix}"


def add_prefix(text: str, prefix: str) -> str:
    return f"{prefix}{text}"


def uppercase(text: str) -> str:
    return text.upper()


def strip_brackets(text: str) -> str:
    return re.sub(r"\[[^\]]+\]", "", text)


def test_leksara_executes_pipeline_in_order():
    pipeline = {
        "patterns": [lambda s: s.replace("buruk", "baik")],
        "functions": [
            (append_suffix, {"suffix": "!"}),
            uppercase,
        ],
    }
    out = leksara(["produk buruk"], pipeline=pipeline)
    assert out == ["PRODUK BAIK!"]


def test_leksara_preserves_non_string_items():
    pipeline = {"patterns": [], "functions": [uppercase]}
    data = ["halo", None, 42]
    out = leksara(data, pipeline=pipeline)
    assert out[0] == "HALO"
    assert out[1] is None
    assert out[2] == 42


def test_leksara_benchmark_returns_metrics():
    pipeline = {"patterns": [], "functions": [(append_suffix, {"suffix": "!"})]}
    result, metrics = leksara(["tes"], pipeline=pipeline, benchmark=True)
    assert result == ["tes!"]
    assert metrics["n_steps"] >= 1
    assert metrics["total_time_sec"] >= 0
    assert all(len(item) == 2 for item in metrics["per_step"])


def test_review_chain_masks_whitelist_tokens():
    chain = ReviewChain.from_steps(functions=[strip_brackets])
    text = "Hubungi [EMAIL] segera"
    out = chain.process_text(text)
    assert "[EMAIL]" in out


def test_review_chain_transform_with_benchmark_list_input():
    chain = ReviewChain([
        (add_prefix, {"prefix": "clean: "}),
        (append_suffix, {"suffix": "!"}),
    ])
    result, metrics = chain.transform(["oke"], benchmark=True)
    assert result == ["clean: oke!"]
    assert metrics["n_steps"] == 2


def test_review_chain_handles_pandas_series():
    chain = ReviewChain([uppercase])
    series = pd.Series(["halo", "dunia"])
    out = chain.transform(series)
    assert list(out) == ["HALO", "DUNIA"]


def test_run_pipeline_with_preset_replaces_phone_number():
    out = run_pipeline(["Hubungi 081234567890"], preset="ecommerce_review")
    assert "[PHONE_NUMBER]" in out[0]


def test_run_pipeline_with_preset_preserves_rating_decimal():
    out = run_pipeline(["rating produk ini 4.0/5"], preset="ecommerce_review")
    assert "4.0" in out[0]
