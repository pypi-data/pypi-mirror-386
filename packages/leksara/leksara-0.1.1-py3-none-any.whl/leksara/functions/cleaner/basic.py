"""Basic cleaning functions: remove_tags, case_normal, remove_stopwords, remove_whitespace, remove_emoji, replace_emoji."""

import html
import re
import os
import string
import json
from pathlib import Path
from functools import lru_cache

TAG_RE = re.compile(r"<[^>]+>")

URL_PATTERN = r'((?:https?|ftp)://|www\.)[\w.-]+(/[\w./?=&%#:-]*)?'
POPULAR_TLDS = ['com', 'id', 'co.id', 'go.id', 'ac.id', 'net', 'org', 'xyz', 'info', 'io']
tlds_pattern_part = "|".join(POPULAR_TLDS)
URL_PATTERN_WITH_PATH = fr'\b[a-zA-Z0-9-]+\.(?:{tlds_pattern_part})\b(/[\w./?=&%#:-]*)?'

try:
    config_path = Path(__file__).resolve().parent.parent.parent / "resources" / "dictionary" / "emoji_dictionary.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        emoji_dictionary = json.load(f)
except Exception as e:
    print(f"Gagal memuat file konfigurasi: {e}")
    emoji_dictionary = {}

def remove_tags(text: str) -> str:
    """Hapus tag HTML dan konversi entitas menjadi karakter biasa.

    - Menghapus tag menggunakan regex sederhana.
    - Mengonversi entitas HTML (&nbsp;, &amp;, &quot;, dsb.) menjadi karakter asli.
    - Mengganti NBSP (\u00A0) menjadi spasi biasa agar mudah dinormalisasi.
    """
    if not isinstance(text, str):
        return text
    
    no_tags = TAG_RE.sub("", text)
    unescaped = html.unescape(no_tags)
    return unescaped.replace("\u00A0", " ")

def case_normal(text: str) -> str:
    """Ubah teks menjadi huruf kecil menggunakan casefold untuk dukungan Unicode."""
    if not isinstance(text, str):
        return text
    return text.casefold()

def remove_stopwords(text):
    """Hapus stopwords Bahasa Indonesia.

    - Menggabungkan daftar stopwords dari NLTK ("indonesian") dan resource lokal `resources/stopwords/id.txt`.
    - Menghapus baik bentuk singkatan (yang tercantum di file lokal) maupun kata lengkap.
    - Tetap mempertahankan tanda baca dan spasi asli.
    """
    if not isinstance(text, str):
        return text

    stopwords_all = _load_id_stopwords()

    tokens = re.findall(r"\w+|\W+", text, flags=re.UNICODE)
    kept = []
    for tok in tokens:
        if re.fullmatch(r"\w+", tok, flags=re.UNICODE):
            if tok.casefold() in stopwords_all:
                continue
        kept.append(tok)

    return "".join(kept)

def remove_whitespace(text):
    """Normalisasi whitespace: trim dan kompres spasi berlebih menjadi satu spasi."""
    if not isinstance(text, str):
        return text
    return re.sub(r"\s+", " ", text).strip()

def remove_digits(text: str) -> str:
    """menghapus bilangan pada teks"""
    if not isinstance(text, str):
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")
    
    return re.sub(r'\d+', '', text)

def remove_punctuation(text: str, exclude: str = None) -> str:
    if not isinstance(text, str):
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")

    if exclude and not isinstance(exclude, str):
        raise TypeError(f"Parameter 'exclude' harus berupa string, tetapi menerima tipe {type(exclude).__name__}")

    ASCII_PUNCTUATION = string.punctuation
    UNICODE_PUNCTUATION = "“”‘’—…"
    punctuation_to_remove = ASCII_PUNCTUATION + UNICODE_PUNCTUATION

    if exclude:
        punctuation_to_remove = ''.join([p for p in punctuation_to_remove if p not in exclude])

    pattern = f"[{re.escape(punctuation_to_remove)}]"
    return re.sub(pattern, '', text)


def replace_url(text: str, mode: str = "remove") -> str:
    if not isinstance(text, str):
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")

    allowed_modes = {"remove", "replace"}
    if mode not in allowed_modes:
        raise ValueError(f"Mode '{mode}' tidak valid. Pilihan yang tersedia adalah {list(allowed_modes)}")

    replacement_token = '[URL]' if mode == "replace" else ''

    text = re.sub(URL_PATTERN, replacement_token, text, flags=re.IGNORECASE)

    text = re.sub(URL_PATTERN_WITH_PATH, replacement_token, text, flags=re.IGNORECASE)

    return text

def remove_emoji(text: str, mode: str = "remove"):
    if not isinstance(text, str):
        raise TypeError(f"Input harus berupa string, tetapi menerima tipe {type(text).__name__}")
    pattern = re.compile("|".join(map(re.escape, emoji_dictionary.keys())))

    allowed_modes = {"remove", "replace"}
    if mode not in allowed_modes:
        raise ValueError(f"Mode '{mode}' tidak valid. Pilihan yang tersedia adalah {list(allowed_modes)}")

    if mode == "remove":
        return pattern.sub('', text)
    elif mode == "replace":
        return pattern.sub(lambda m: f" {emoji_dictionary.get(m.group(0), '')} ", text)

    return text


@lru_cache(maxsize=1)
def _load_id_stopwords():
    """Muat stopwords Bahasa Indonesia dari file lokal: leksara/resources/stopwords/id.txt.

    Mengembalikan set berisi stopword dalam bentuk casefolded.
    Jika file tidak ditemukan, mengembalikan set kosong.
    """
    stopwords_local = set()
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        resource_path = os.path.join(base_dir, "resources", "stopwords", "id.txt")
        if os.path.exists(resource_path):
            with open(resource_path, encoding="utf-8") as f:
                for line in f:
                    w = line.strip()
                    if w and not w.startswith("#"):
                        stopwords_local.add(w.casefold())
    except Exception:
        return set()

    return stopwords_local