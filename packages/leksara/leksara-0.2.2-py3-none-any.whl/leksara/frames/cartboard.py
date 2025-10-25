"""CartBoard: capture raw reviews and generate initial metadata flags.

Fitur
- Membersihkan teks (hapus email, URL, tanda baca, stopwords) menggunakan utilitas internal Leksara.
- Menghasilkan metadata flags:
    - pii_flag: ada PII (email/telepon/NIK/alamat)
    - non_alphabetical_flag: ada karakter non-alfabet (angka/simbol)

Example
-------
>>> from leksara.frames.cartboard import CartBoard
>>> text = "Barangnya mantulll! Email saya: user@example.com. Visit https://shop.id"
>>> board = CartBoard(text, rating=5)
>>> result = board.to_dict()
>>> sorted(result.keys())
['non_alphabetical_flag', 'original_text', 'pii_flag', 'rating']
>>> result['pii_flag']  # email detected
True
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import re
import unicodedata

import pandas as pd
try:
    from emoji import emoji_list as _emoji_list
except Exception:  # pragma: no cover - optional dependency
    _emoji_list = None

# Cleaning utilities from project
from ..functions.cleaner.basic import (
    TAG_RE,
    URL_PATTERN,
    URL_PATTERN_WITH_PATH,
    remove_digits,
    remove_emoji,
    remove_punctuation,
    remove_tags,
    replace_url,
    _load_id_stopwords,
    emoji_dictionary,
)
from ..functions.patterns.pii import (
    replace_email,
    replace_phone,
    replace_address,
    replace_id,
    email_config,
    phone_config,
    NIK_config,
    address_config,
)
from ..functions.review.advanced import replace_rating


_EMOJI_PATTERN = re.compile("|".join(map(re.escape, emoji_dictionary.keys()))) if emoji_dictionary else re.compile(r"$^")

DEFAULT_NON_ALPHA_THRESHOLD = 0.15
_RATING_FRACTION_PATTERN = re.compile(r"\b\d+/\d+\b")
_REPEATED_SYMBOL_PATTERN = re.compile(r"([!?#*]){2,}")
_ADDRESS_MERGE_THRESHOLD = 10


def _load_rating_patterns() -> List[re.Pattern]:
    try:
        config_path = Path(__file__).resolve().parent.parent / "resources" / "regex_patterns" / "rating_patterns.json"
        with open(config_path, encoding="utf-8") as fh:
            data = json.load(fh)
        patterns: List[str] = []
        if isinstance(data, dict):
            for item in data.get("rules", []):
                if isinstance(item, dict):
                    patt = item.get("pattern")
                    if isinstance(patt, str):
                        patterns.append(patt)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    patt = item.get("pattern")
                    if isinstance(patt, str):
                        patterns.append(patt)
                elif isinstance(item, str):
                    patterns.append(item)
        compiled: List[re.Pattern] = []
        for patt in patterns:
            try:
                compiled.append(re.compile(patt, flags=re.IGNORECASE))
            except re.error:
                continue
        return compiled
    except Exception:
        return []


_RATING_PATTERNS = _load_rating_patterns()


def _get_id_stopwords_full() -> set[str]:
    """Load full Indonesian stopwords from resources using existing loader."""
    try:
        return _load_id_stopwords() or set()
    except Exception:
        return set()


def _ensure_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _strip_html(text: str) -> str:
    return remove_tags(text)


def _tokenize_words(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z]+", text.casefold())


def _count_id_stopwords(tokens: Iterable[str]) -> int:
    stopwords = _get_id_stopwords_full()
    return sum(1 for token in tokens if token in stopwords)


def _calc_non_alpha_ratio(text: str) -> float:
    relevant = [ch for ch in text if not ch.isspace() and not ch.isdigit()]
    if not relevant:
        return 0.0
    non_alpha = sum(1 for ch in relevant if not ch.isalpha())
    return non_alpha / len(relevant)


def _has_non_alpha_noise(text: str) -> bool:
    if _extract_emojis(text):
        return True
    if _RATING_FRACTION_PATTERN.search(text):
        return True
    if "@" in text:
        return True
    if _REPEATED_SYMBOL_PATTERN.search(text):
        return True
    return False


def _has_rating(text: str) -> bool:
    processed = replace_rating(text)
    if processed != text:
        return True
    for patt in _RATING_PATTERNS:
        if patt.search(text):
            return True
    return False


def _extract_urls(text: str) -> List[str]:
    urls = re.findall(URL_PATTERN, text, flags=re.IGNORECASE)
    urls_with_path = re.findall(URL_PATTERN_WITH_PATH, text, flags=re.IGNORECASE)
    combined = []
    combined.extend("".join(url) if isinstance(url, tuple) else url for url in urls)
    combined.extend(url if isinstance(url, str) else "".join(url) for url in urls_with_path)
    return [u for u in combined if u]


def _extract_html_tags(text: str) -> List[str]:
    return TAG_RE.findall(text)


def _extract_emails(text: str) -> List[str]:
    pattern = email_config.get("pattern", "")
    if not pattern:
        return []
    return re.findall(pattern, text, flags=re.IGNORECASE)


def _normalize_phone(potential_number: str) -> Optional[str]:
    cleaned_number = re.sub(r'[-\s]', '', potential_number)
    normalized_number: Optional[str] = None
    if cleaned_number.startswith(('+62', '62')):
        normalized_number = '0' + re.sub(r'^\+?62', '', cleaned_number)
    elif cleaned_number.startswith('0'):
        normalized_number = cleaned_number
    if normalized_number and 10 <= len(normalized_number) <= 13:
        return normalized_number
    return None


def _extract_phones(text: str) -> Dict[str, List[str]]:
    pattern = phone_config.get("pattern", "")
    raw_numbers: List[str] = []
    normalized_numbers: List[str] = []

    if pattern:
        for m in re.finditer(pattern, text):
            raw_value = m.group(0)
            if raw_value not in raw_numbers:
                raw_numbers.append(raw_value)
            normalized = _normalize_phone(raw_value)
            if normalized and normalized not in normalized_numbers:
                normalized_numbers.append(normalized)

    # Fallback extractor captures long digit sequences with separators (spaces/dashes)
    fallback_pattern = re.compile(r"(?<!\w)(\+?\d[\d\s-]{6,}\d)(?!\d)")
    for m in fallback_pattern.finditer(text):
        raw_value = m.group(0)
        trimmed_value = raw_value.strip()
        if trimmed_value not in raw_numbers:
            raw_numbers.append(trimmed_value)
        normalized = _normalize_phone(trimmed_value)
        if normalized and normalized not in normalized_numbers:
            normalized_numbers.append(normalized)
    return {"raw": raw_numbers, "normalized": normalized_numbers}


def _extract_emojis(text: str) -> List[str]:
    results: List[str] = []
    if _EMOJI_PATTERN.pattern != r"$^":
        results.extend(_EMOJI_PATTERN.findall(text))
    if _emoji_list is not None:
        try:
            for item in _emoji_list(text):
                emoji_char = item.get("emoji")
                if emoji_char:
                    results.append(emoji_char)
        except Exception:
            pass
    if not results:
        for char in text:
            if char.isalnum() or char.isspace():
                continue
            if unicodedata.category(char) in {"So", "Sk"}:
                results.append(char)
    ordered_unique: List[str] = []
    for emoji_char in results:
        if emoji_char not in ordered_unique:
            ordered_unique.append(emoji_char)
    return ordered_unique


def _extract_addresses(text: str) -> List[str]:
    trigger_pattern = address_config.get("trigger_pattern", {}).get("pattern", "")
    if trigger_pattern and not re.search(trigger_pattern, text, flags=re.IGNORECASE):
        return []

    components = address_config.get("components", {})
    spans: List[Tuple[int, int]] = []
    for comp in components.values():
        pattern = comp.get("pattern")
        if not pattern:
            continue
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            start, end = match.start(), match.end()
            while end < len(text) and text[end] in " ,.;:":
                end += 1
            spans.append((start, end))

    if not spans:
        return []

    spans.sort()
    merged: List[Tuple[int, int]] = []
    for start, end in spans:
        if merged:
            prev_start, prev_end = merged[-1]
            gap = start - prev_end
            if gap <= _ADDRESS_MERGE_THRESHOLD and not re.search(r"[.?!]", text[prev_end:start]):
                merged[-1] = (prev_start, max(prev_end, end))
                continue
        merged.append((start, end))

    results: List[str] = []
    seen: set[str] = set()
    for start, end in merged:
        snippet = text[start:end].strip(" ,.;:")
        if not snippet:
            continue
        key = snippet.casefold()
        if key in seen:
            continue
        seen.add(key)
        results.append(snippet)
    return results


def _extract_ids(text: str) -> List[str]:
    pattern = NIK_config.get("pattern", "")
    if not pattern:
        return []
    results: List[str] = []
    seen: set[str] = set()
    for match in re.finditer(pattern, text):
        snippet = match.group(0).strip()
        if not snippet:
            continue
        if snippet in seen:
            continue
        seen.add(snippet)
        results.append(snippet)
    return results


def _pii_flag_from_text(text: str) -> bool:
    email_result = replace_email(text, mode="replace")
    phone_result = replace_phone(text, mode="replace")
    address_result = replace_address(text, mode="replace")
    id_result = replace_id(text, mode="replace")
    return any(
        token in result
        for token, result in (
            ("[EMAIL]", email_result),
            ("[PHONE_NUMBER]", phone_result),
            ("[ADDRESS]", address_result),
            ("[NIK]", id_result),
        )
    )


def _build_flag_record(text: str, *, non_alpha_threshold: float) -> Dict[str, Any]:
    stripped = _strip_html(text)
    rating_flag = _has_rating(stripped)
    pii_flag = _pii_flag_from_text(stripped)
    non_alpha_ratio = _calc_non_alpha_ratio(stripped)
    non_alpha_noise = non_alpha_ratio > non_alpha_threshold or _has_non_alpha_noise(stripped)
    record: Dict[str, Any] = {
        "original_text": text,
        "rating_flag": rating_flag,
        "pii_flag": pii_flag,
        "non_alphabetical_flag": non_alpha_noise,
    }
    return record


def _build_stats_record(text: str) -> Dict[str, Any]:
    stripped = _strip_html(text)
    tokens = _tokenize_words(stripped)
    stopword_count = _count_id_stopwords(tokens)
    punctuation_removed = len(stripped) - len(remove_punctuation(stripped))
    symbols_removed = len(stripped) - len(remove_digits(stripped))
    emojis = _extract_emojis(stripped)
    urls = _extract_urls(stripped)
    html_tags = _extract_html_tags(text)
    emails = _extract_emails(stripped)
    phones = _extract_phones(stripped)
    addresses = _extract_addresses(stripped)
    ids_found = _extract_ids(stripped)
    noise_types = [urls, html_tags, emails, phones["raw"], emojis, addresses, ids_found]
    noise_count = sum(1 for items in noise_types if items)
    return {
        "length": len(stripped),
        "word_count": len(tokens),
        "stopwords": stopword_count,
        "punctuations": punctuation_removed,
        "symbols": symbols_removed,
        "emojis": len(emojis),
        "noise_count": noise_count,
        "urls": urls,
        "html_tags": html_tags,
        "emails": emails,
        "phones": phones["raw"],
        "phones_normalized": phones["normalized"],
        "emoji_list": emojis,
        "addresses": addresses,
        "ids": ids_found,
    }


def _build_noise_record(text: str) -> Dict[str, List[str]]:
    stripped = _strip_html(text)
    urls = _extract_urls(stripped)
    replace_url(stripped, mode="replace")
    html_tags = _extract_html_tags(text)
    emails = _extract_emails(stripped)
    replace_email(stripped, mode="replace")
    phones = _extract_phones(stripped)
    replace_phone(stripped, mode="replace")
    emojis = _extract_emojis(stripped)
    remove_emoji(stripped, mode="remove")
    addresses = _extract_addresses(stripped)
    ids_found = _extract_ids(stripped)
    return {
        "urls": urls,
        "html_tags": html_tags,
        "emails": emails,
        "phones": phones["raw"],
        "phones_normalized": phones["normalized"],
        "emojis": emojis,
        "addresses": addresses,
        "ids": ids_found,
    }


def _coerce_frame(data: Any, text_column: str = "text") -> Tuple[pd.DataFrame, str]:
    if isinstance(data, pd.DataFrame):
        frame = data.copy()
        candidates = [text_column, "review_text", "product_text", "text"]
        for candidate in candidates:
            if candidate in frame.columns:
                text_column = candidate
                break
        else:
            raise KeyError(f"Column '{text_column}' not found in DataFrame")
        frame[text_column] = frame[text_column].apply(_ensure_text)
        return frame, text_column
    if isinstance(data, pd.Series):
        frame = data.to_frame(name=text_column)
        frame[text_column] = frame[text_column].apply(_ensure_text)
        return frame, text_column
    if isinstance(data, str):
        frame = pd.DataFrame({text_column: [_ensure_text(data)]})
        return frame, text_column
    if isinstance(data, Iterable):
        frame = pd.DataFrame({text_column: [_ensure_text(item) for item in data]})
        return frame, text_column
    raise TypeError("Unsupported input type for text collection")


def get_flags(
    data: Any,
    *,
    non_alpha_threshold: float = DEFAULT_NON_ALPHA_THRESHOLD,
    merge_input: bool = True,
    text_column: str = "text",
) -> pd.DataFrame:
    frame, resolved_column = _coerce_frame(data, text_column)
    texts = frame[resolved_column]
    records = [
        _build_flag_record(text, non_alpha_threshold=non_alpha_threshold)
        for text in texts
    ]
    df = pd.DataFrame(records)
    df.index = texts.index
    if merge_input:
        if "original_text" in df.columns:
            df = df.drop(columns=["original_text"])
        return pd.concat([frame, df], axis=1)
    return df


def get_stats(
    data: Any,
    *,
    merge_input: bool = True,
    as_dict: bool = True,
    text_column: str = "text",
) -> pd.DataFrame:
    frame, resolved_column = _coerce_frame(data, text_column)
    texts = frame[resolved_column]
    records = [_build_stats_record(text) for text in texts]
    if as_dict:
        stats_series = pd.Series(records, index=texts.index, name="stats")
        result = frame.copy() if merge_input else pd.DataFrame(index=texts.index)
        result["stats"] = stats_series
        return result
    df = pd.DataFrame(records, index=texts.index)
    return pd.concat([frame, df], axis=1) if merge_input else df


def noise_detect(
    data: Any,
    *,
    merge_input: bool = True,
    include_normalized: bool = True,
    text_column: str = "text",
) -> pd.DataFrame:
    frame, resolved_column = _coerce_frame(data, text_column)
    texts = frame[resolved_column]
    records = [_build_noise_record(text) for text in texts]
    if not include_normalized:
        for record in records:
            record.pop("phones_normalized", None)
    noise_series = pd.Series(records, index=texts.index, name="detect_noise")
    if merge_input:
        result = frame.copy()
        result["detect_noise"] = noise_series
        return result
    return noise_series.to_frame()


@dataclass
class CartBoard:
    original_text: str
    rating: Optional[float] = None

    def __init__(self, raw_text: str, rating: Optional[float] = None):
        if not isinstance(raw_text, str):
            raise TypeError(f"raw_text must be str, got {type(raw_text).__name__}")
        self.original_text = raw_text
        self.rating = rating
        self._flags = self._generate_flags(raw_text)

    # --------------- public API ---------------
    @property
    def pii_flag(self) -> bool:
        return self._flags["pii_flag"]

    @property
    def non_alphabetical_flag(self) -> bool:
        return self._flags["non_alphabetical_flag"]

    def to_dict(self) -> Dict[str, Optional[object]]:
        return {
            "original_text": self.original_text,
            "rating": self.rating,
            "pii_flag": self.pii_flag,
            "non_alphabetical_flag": self.non_alphabetical_flag,
        }

    # --------------- internals ---------------
    def _generate_flags(self, text: str) -> Dict[str, bool]:
        df = get_flags(
            [text],
            merge_input=False,
            non_alpha_threshold=DEFAULT_NON_ALPHA_THRESHOLD,
        )
        record = df.iloc[0]
        return {
            "pii_flag": bool(record["pii_flag"]),
            "non_alphabetical_flag": bool(record["non_alphabetical_flag"]),
        }
