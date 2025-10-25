"""Advanced review mining: rating, elongation, acronym, slang, contraction, normalization."""

import re
import pandas as pd
import json
from pathlib import Path
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# buat stemmer sekali saja (hemat waktu)
_factory = StemmerFactory()
_STEMMER = _factory.create_stemmer()


def _normalize_rating_config(raw_config):
    if isinstance(raw_config, dict):
        rules = raw_config.get('rules', [])
        blacklist = raw_config.get('blacklist', [])
        flags = raw_config.get('defaults', {}).get('flags', [])
        return raw_config, rules, blacklist, flags
    if isinstance(raw_config, list):
        normalized = {
            "rules": raw_config,
            "blacklist": [],
            "defaults": {"flags": []},
        }
        return normalized, raw_config, [], []
    return {}, [], [], []


def _load_rating_config(config_path: Path | None = None):
    """Muat konfigurasi rating dan kembalikan bentuk ternormalisasi."""
    target_path = config_path
    if target_path is None:
        target_path = Path(__file__).resolve().parent.parent.parent / "resources" / "regex_patterns" / "rating_rules.json"

    with open(target_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    return _normalize_rating_config(raw)


try:
    base_regex_path = Path(__file__).resolve().parent.parent.parent / "resources" / "regex_patterns"
    candidate_paths = [
        base_regex_path / "rating_patterns.json",
        base_regex_path / "rating_rules.json",
    ]

    last_error: Exception | None = None
    for candidate in candidate_paths:
        try:
            _RATING_CONFIG, rules, blacklist, _FLAGS = _load_rating_config(candidate)
            break
        except FileNotFoundError as err:
            last_error = err
            continue
    else:
        if last_error:
            raise last_error
        raise FileNotFoundError("Rating config tidak ditemukan.")

    _SORTED_RULES = sorted(rules, key=lambda r: r.get('priority', 0), reverse=True)
    _BLACKLIST_PATTERNS = [re.compile(item['pattern'], re.IGNORECASE | re.MULTILINE) for item in blacklist]
except Exception as e:
    print(f"Gagal memuat file konfigurasi: {e}")
    _RATING_CONFIG = {}
    _SORTED_RULES = []
    _BLACKLIST_PATTERNS = []
    _FLAGS = []

try:
    dict_path = Path(__file__).resolve().parent.parent.parent / "resources" / "dictionary" / "acronym_dict.json"
    rules_path = Path(__file__).resolve().parent.parent.parent / "resources" / "dictionary" / "dictionary_rules.json"
    contractions_path = Path(__file__).resolve().parent.parent.parent / "resources" / "dictionary" / "contractions_dict.json" 
    slangs_path = Path(__file__).resolve().parent.parent.parent / "resources" / "dictionary" / "slangs_dict.json" 
    with open(dict_path, 'r', encoding='utf-8') as f:
        _ACRONYM_DICT = json.load(f)
    with open(rules_path, 'r', encoding='utf-8') as f:
        rules_data = json.load(f).get("sections", {}).get("acronym", {}).get("conflict_rules", [])
        _CONFLICT_RULES = {rule["token"]: rule for rule in rules_data}
    with open(contractions_path, 'r', encoding='utf-8') as f:
        _CONTRACTIONS_DICT = json.load(f)
    with open(slangs_path, 'r', encoding='utf-8') as f:
        _SLANGS_DICT = json.load(f)
except Exception as e:
    print(f"Gagal memuat file konfigurasi akronim: {e}")
    _ACRONYM_DICT = {}
    _CONFLICT_RULES = {}
    _CONTRACTIONS_DICT = {}

def replace_rating(text: str) -> str:
    if not isinstance(text, str) or not text:
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")

    flag_pattern = 0
    for pattern in _FLAGS:
        flag_object = getattr(re, pattern.upper(), 0)
        flag_pattern |= flag_object

    processed_text = text
    placeholder_map = {}
    counter = [0]

    def make_placeholder(val):
        idx = counter[0]
        counter[0] += 1
        ph = f"__RATING_{idx}__"
        placeholder_map[ph] = val
        return ph

    for rule in _SORTED_RULES:
        initial_pattern = rule.get("trigger_pattern", rule.get("pattern", ""))

        def replacer(match):
            matched_text = match.group(0)

            for bp in _BLACKLIST_PATTERNS:
                if bp.match(matched_text):
                    return matched_text

            raw_value = None
            rule_type = rule.get('type')

            if rule_type == 'extract':
                vg = rule.get('value_group', 0)
                try:
                    raw_value = match.group(vg)
                except IndexError:
                    raw_value = None

            elif rule_type in ['extract_multi', 'extract_or_map']:
                target_match = match
                if "trigger_pattern" in rule:
                    extraction_pattern = rule.get("pattern", "")
                    extraction_match = re.search(extraction_pattern, matched_text, flags=flag_pattern)
                    if not extraction_match:
                        return matched_text
                    target_match = extraction_match

                value_group_list = rule.get('value_groups') or ([rule.get('value_group')] if 'value_group' in rule else [])
                word_group_list = rule.get('word_groups') or ([rule.get('word_group')] if 'word_group' in rule else [])

                for group_idx in value_group_list:
                    if group_idx and group_idx <= len(target_match.groups()) and target_match.group(group_idx):
                        captured_value = target_match.group(group_idx).lower()
                        if re.fullmatch(r'\d+(?:[.,]\d+)?', captured_value):
                            raw_value = captured_value
                            break

                if raw_value is None:
                    for group_idx in word_group_list:
                        if group_idx and group_idx <= len(target_match.groups()) and target_match.group(group_idx):
                            word = target_match.group(group_idx).lower()
                            raw_value = rule.get('word_map', {}).get(word)
                            if raw_value is not None:
                                break

            elif rule_type == 'emoji_or_mult':
                mult_group_idx = rule.get('mult_group')
                if mult_group_idx and mult_group_idx <= len(match.groups()) and match.group(mult_group_idx):
                    try:
                        rating = float(match.group(mult_group_idx))
                        return str(round(rating, 2))
                    except Exception:
                        return matched_text
                else:
                    count = sum(matched_text.count(e) for e in rule.get('emojis', []))
                    if count > 0:
                        return str(round(count, 2))
                    return matched_text

            if raw_value is None: return matched_text

            str_value = str(raw_value)
            for old, new in rule.get('postprocess', {}).get('replace', {}).items():
                str_value = str_value.replace(old, new)

            try:
                str_value = str_value.replace('½', '.5').replace('1/2', '.5')
                rating = float(str_value)

                if 'scale_denominator_group' in rule:
                    scale_group_idx = rule['scale_denominator_group']
                    scale_str = None
                    try:
                        scale_str = match.group(scale_group_idx)
                    except IndexError:
                        m2 = re.search(rule.get('pattern', ''), matched_text, flags=flag_pattern)
                        if m2:
                            try:
                                scale_str = m2.group(scale_group_idx)
                            except IndexError:
                                scale_str = None

                    if scale_str is not None:
                        scale = float(scale_str.replace(',', '.'))
                        if scale != 5.0 and scale > 0:
                            rating = (rating / scale) * 5.0

                min_val, max_val = rule.get('clamp', [None, None])
                if min_val is not None and rating < min_val:
                    rating = min_val
                if max_val is not None and rating > max_val:
                    rating = max_val


                final_string = str(round(rating, 2))
                ph = make_placeholder(final_string)

                if "trigger_pattern" in rule and rule.get("pattern"):
                    try:
                        new_inner = re.sub(rule.get("pattern", ""), ph, matched_text, count=1, flags=flag_pattern)
                        return new_inner
                    except re.error:
                        leading = re.match(r'^\s*', matched_text).group(0)
                        trailing = re.search(r'\s*$', matched_text).group(0)
                        return f"{leading}{ph}{trailing}"

                leading = re.match(r'^\s*', matched_text).group(0)
                trailing = re.search(r'\s*$', matched_text).group(0)
                return f"{leading}{ph}{trailing}"

            except Exception:
                return matched_text
        processed_text = re.sub(initial_pattern, replacer, processed_text, flags=flag_pattern)
    
    for ph, val in placeholder_map.items():
        processed_text = processed_text.replace(ph, val)
    
    processed_text = re.sub(r'\s{2,}', ' ', processed_text).strip()
    return processed_text

def shorten_elongation(text: str, max_repeat: int = 2) -> str:
    """Kurangi pengulangan karakter hingga maksimal `max_repeat` kemunculan.

    Contoh: mantuuulll -> mantul (dengan max_repeat=1 atau 2 sesuai preferensi)
    
    TODO: Implementasi fungsi ini oleh kontributor selanjutnya.
    """
    if max_repeat < 1:
        raise ValueError("max_repeat must be >= 1")

    # Regex: (.)\1{n,} menangkap karakter yang diulang lebih dari n kali
    else:
        pattern = re.compile(r"(.)\1{" + str(max_repeat) + r",}")
        text = pattern.sub(lambda m: m.group(1) * max_repeat, text)

    return text

def replace_acronym(text: str, mode: str = "remove")-> str:
    if not isinstance(text, str):
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")

    allowed_modes = {"remove", "replace"}
    if mode not in allowed_modes:
        raise ValueError(f"Mode '{mode}' tidak valid. Pilihan yang tersedia adalah {list(allowed_modes)}")

    pattern = re.compile(r'\b(' + '|'.join(re.escape(key) for key in _ACRONYM_DICT.keys()) + r')\b', re.IGNORECASE)

    def replacer(match):
        acronym = match.group(0).lower()
        replacement = None

        if acronym in _CONFLICT_RULES:
            conflict = _CONFLICT_RULES[acronym]
            for rule in conflict.get("rules", []):
                if re.search(rule["context_pattern"], text, re.IGNORECASE):
                    replacement = rule["preferred"]
                    break
            if replacement is None:
                return match.group(0)
        else:
            standard_replacement = _ACRONYM_DICT.get(acronym)
            if isinstance(standard_replacement, list):
                replacement = standard_replacement[0]
            else:
                replacement = standard_replacement

        if mode == "replace":
            return replacement
        elif mode == "remove":
            return ""

    return pattern.sub(replacer, text)


def normalize_slangs(text: str, mode: str = "replace") -> str:
    """Normalisasi slang dengan kamus."""
    if not isinstance(text, str):
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")

    allowed_modes = {"remove", "replace"}
    if mode not in allowed_modes:
        raise ValueError(f"Mode '{mode}' tidak valid. Pilihan yang tersedia adalah {list(allowed_modes)}")

    if not _SLANGS_DICT:
        return text

    # Kompilasi pola sekali per pemanggilan (kamus relatif kecil)
    pattern = re.compile(r'\b(' + '|'.join(re.escape(key) for key in _SLANGS_DICT.keys()) + r')\b', re.IGNORECASE)

    def replacer(match):
        token = match.group(0).lower()
        replacement = None

        # Aturan konflik (jika ada di rules file)
        if token in _CONFLICT_RULES:
            conflict = _CONFLICT_RULES[token]
            for rule in conflict.get("rules", []):
                if re.search(rule.get("context_pattern", ""), text, re.IGNORECASE):
                    replacement = rule.get("preferred")
                    break
            if replacement is None:
                # Jika tak ada konteks yang cocok → pertahankan apa adanya
                return match.group(0)
        else:
            std = _SLANGS_DICT.get(token)
            if isinstance(std, list) and std:
                replacement = std[0]
            else:
                replacement = std

        if mode == "replace":
            return replacement if replacement is not None else match.group(0)
        else:  # mode == "remove"
            return ""

    return pattern.sub(replacer, text)

# Untuk mempertahankan format kapitalisasi saat expand_contraction
def _preserve_case(original: str, expansion: str) -> str:
    if not original:
        return expansion
    try:
        if original.isupper():
            return expansion.upper()
        if len(original) > 1 and original[0].isupper() and original[1:].islower():
            return expansion.capitalize()
        if len(original) == 1 and original.isupper():
            return expansion.upper()
    except Exception:
        pass
    return expansion

def expand_contraction(text: str) -> str:
    """
    Expand contractions using `leksara/resources/dictionary/contractions_dict.json`.

    Behaviors:
    - case-insensitive matching on whole-word boundaries
    - preserve capitalization style of the original token
    - tolerant jika kamus tidak ada / kosong -> kembalikan teks semula
    """
    if not isinstance(text, str):
        # bukan string, kembalikan apa adanya
        return text

    contractions = _CONTRACTIONS_DICT or {}
    if not contractions:
        return text

    # Buat key list, gunakan lower-case keys untuk lookup konsisten.
    keys = sorted((str(k) for k in contractions.keys()), key=len, reverse=True)
    alternation = "|".join(re.escape(k) for k in keys)
    
    # menggunakan lookaround untuk lebih aman: (?<!\w)(key)(?!\w)
    try:
        pattern = re.compile(rf"(?<!\w)({alternation})(?!\w)", flags=re.IGNORECASE)
    except re.error:
        # jika alternation terlalu panjang atau ada karakter aneh -> fallback: loop manual per key
        pattern = None

    def _replace_with_preserve(m: re.Match) -> str:
        orig = m.group(0)
        key = orig.lower()
        expansion = contractions.get(key)
        if expansion is None:
            # fallback: coba raw key atau return original
            expansion = contractions.get(orig, orig)
        return _preserve_case(orig, str(expansion))

    if pattern is not None:
        try:
            return pattern.sub(_replace_with_preserve, text)
        except Exception:
            # kalau gagal, fallback ke loop manual di bawah
            pass

    # Fallback safe: lakukan penggantian per-key menggunakan word boundaries yang sederhana
    out = text
    for k in keys:
        k_esc = re.escape(k)
        try:
            pat = re.compile(rf"(?<!\w)({k_esc})(?!\w)", flags=re.IGNORECASE)
            out = pat.sub(lambda m: _preserve_case(m.group(0), str(contractions.get(m.group(0).lower(), m.group(0)))), out)
        except re.error:
            continue
    return out

# Deteksi placeholder whitelist (Private Use Area) agar tidak di-stem
def _is_masked_whitelist_token(token: str) -> bool:
    return any(0xE000 <= ord(ch) <= 0xF8FF for ch in token)

def _is_bracket_token(token: str) -> bool:
    return len(token) >= 2 and token.startswith("[") and token.endswith("]")

def word_normalization(
    text: str,
    *,
    method: str = "stem",
    word_list=None,
    mode: str = "keep",
) -> str:
    """Normalisasi kata dengan stemming/lemmatization.

    Args:
        text: input string
        method: "stem" (default, pakai Sastrawi), "lemma" (future).
        word_list: daftar kata spesial (list[str])
        mode: 
            - "keep": jangan stem kata dalam word_list
            - "only": hanya stem kata dalam word_list
    """
    if not isinstance(text, str):
        return text

    if word_list is None:
        word_list = []

    word_set = {w.lower() for w in word_list}
    words = text.split()
    out = []

    if method == "stem":
        if mode == "keep":
            for w in words:
                # Lindungi placeholder whitelist dan token bracket
                if _is_masked_whitelist_token(w) or _is_bracket_token(w):
                    out.append(w)
                else:
                    out.append(w if w.lower() in word_set else _STEMMER.stem(w))
        elif mode == "only":
            for w in words:
                if _is_masked_whitelist_token(w) or _is_bracket_token(w):
                    out.append(w)
                else:
                    out.append(_STEMMER.stem(w) if w.lower() in word_set else w)
        else:
            raise ValueError("mode harus 'keep' atau 'only'")
    else:
        # kalau nanti ada lemmatizer lain
        out = words

    return " ".join(out)
