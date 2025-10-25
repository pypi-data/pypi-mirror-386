"""PII cleaning: remove/replace phone, address, email, id."""
import os
import re
import json
from pathlib import Path

try:
    config_path1 = Path(__file__).resolve().parent.parent.parent / "resources" / "regex_patterns" / "pii_patterns.json"
    config_path2 = Path(__file__).resolve().parent.parent.parent / "resources" / "dictionary" / "city_dict.json"
    with open(config_path1, 'r', encoding='utf-8') as f:
        PII_CONFIG = json.load(f)

    with open(config_path2, "r", encoding="utf-8") as f:
        daftar_kota = json.load(f)
except Exception as e:
    print(f"Gagal memuat file konfigurasi: {e}")
    PII_CONFIG = {}
    daftar_kota = {}

address_config = PII_CONFIG.get("pii_address", {})
email_config = PII_CONFIG.get("pii_email", {})
NIK_config = PII_CONFIG.get("pii_nik", {})
phone_config = PII_CONFIG.get("pii_phone", {})


def replace_phone(text: str, mode: str = "remove") -> str:
    if not isinstance(text, str):
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")

    allowed_modes = {"remove", "replace"}
    if mode not in allowed_modes:
        raise ValueError(f"Mode '{mode}' tidak valid. Pilihan yang tersedia adalah {list(allowed_modes)}")

    replacement_token = '[PHONE_NUMBER]' if mode == "replace" else ''


    def validate_and_replace(match):
        potential_number = match.group(0).strip()
        potential_number = re.sub(r'^\(\+62\)', '+62', potential_number)
        potential_number = re.sub(r'(\+?62)\s+', r'\1', potential_number)
        cleaned_number = re.sub(r'[-\s]', '', potential_number)

        normalized_number = None
        if cleaned_number.startswith(('+62', '62')):
            normalized_number = '0' + re.sub(r'^\+?62', '', cleaned_number)
        elif cleaned_number.startswith('0'):
            normalized_number = cleaned_number

        if normalized_number and 10 <= len(normalized_number) <= 13:
            return replacement_token

        return potential_number

    PHONE_PATTERN = phone_config.get("pattern", "")
    result = re.sub(PHONE_PATTERN, validate_and_replace, text)

    result = re.sub(r'\s{2,}', ' ', result).strip()
    return result

def replace_address(text: str, mode: str = "remove", **kwargs) -> str:
    if not isinstance(text, str):
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")

    allowed_modes = {"remove", "replace"}
    if mode not in allowed_modes:
        raise ValueError(f"Mode '{mode}' tidak valid. Pilihan yang tersedia adalah {list(allowed_modes)}")

    replacement_token = '[ADDRESS]' if mode == "replace" else ''

    trigger_config = address_config.get("trigger_pattern", {})
    trigger_pattern = trigger_config.get("pattern", "")
    address_components = address_config.get("components", {})

    if not re.search(trigger_pattern, text, flags=re.IGNORECASE):
        return text

    component_keys = list(address_components.keys())
    normalized_key_map = {
        cid.replace("pii_addr_", ""): cid for cid in component_keys
    }

    if kwargs:
        invalid_keys = [key for key in kwargs if key not in normalized_key_map]
        if invalid_keys:
            invalid_list = ", ".join(sorted(invalid_keys))
            raise KeyError(f"Unknown address component(s): {invalid_list}")

    active_components = []
    for cid, comp_data in address_components.items():
        normalized = cid.replace("pii_addr_", "")
        if kwargs and not kwargs.get(normalized, False):
            continue
        active_components.append((cid, comp_data))

    matches = []
    for comp_id, comp in active_components:
        pattern = comp['pattern']
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            start, end = m.start(), m.end()

            while end < len(text) and text[end] in " ,.;:":
                end += 1
            snippet = text[start:end]
            if comp_id == "pii_addr_house" and not re.search(r"\d", snippet):
                continue
            matches.append((start, end))

    if not matches:
        return text

    matches.sort()
    merged = []
    MERGE_THRESHOLD = 10

    for start, end in matches:
        if not merged:
            merged.append([start, end])
        else:
            prev_start, prev_end = merged[-1]
            gap = start - prev_end
            if gap <= MERGE_THRESHOLD and not re.search(r'[.?!]', text[prev_end:start]):
                merged[-1][1] = end
            else:
                merged.append([start, end])

    result = []
    last_idx = 0
    for start, end in merged:
        result.append(text[last_idx:start])
        if replacement_token:
            result.append(' ' + replacement_token + ' ')
        last_idx = end
    result.append(text[last_idx:])
    processed_text = ''.join(result)

    def remove_city_after_mask(match):
        full_match = match.group(0)
        next_word = match.group(1)
        if next_word and next_word.strip(",. ").upper() in daftar_kota:
            return replacement_token
        return full_match

    processed_text = re.sub(
        rf'{re.escape(replacement_token)}\s+([A-Z][a-z]+)',
        remove_city_after_mask,
        processed_text,
        flags=re.IGNORECASE
    )

    processed_text = re.sub(r'\s*([,.;:])\s*', r'\1 ', processed_text)
    processed_text = re.sub(r'([,.;:]){2,}', r'\1', processed_text)
    processed_text = re.sub(r'\s{2,}', ' ', processed_text).strip()
    return processed_text


def replace_email(text: str, mode: str = "remove")-> str:
    if not isinstance(text, str):
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")

    allowed_modes = {"remove", "replace"}
    if mode not in allowed_modes:
        raise ValueError(f"Mode '{mode}' tidak valid. Pilihan yang tersedia adalah {list(allowed_modes)}")

    replacement_token = '[EMAIL]' if mode == "replace" else ''

    EMAIL_PATTERN = email_config.get("pattern", "")
    return re.sub(EMAIL_PATTERN, replacement_token, text)


def replace_id(text: str, mode: str = "remove") -> str:
    if not isinstance(text, str):
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")

    allowed_modes = {"remove", "replace"}
    if mode not in allowed_modes:
        raise ValueError(f"Mode '{mode}' tidak valid. Pilihan yang tersedia adalah {list(allowed_modes)}")

    replacement_token = '[NIK]' if mode == "replace" else ''

    NIK_PATTERN = NIK_config.get("pattern", "")
    return re.sub(NIK_PATTERN, replacement_token, text)