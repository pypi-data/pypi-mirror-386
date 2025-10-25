"""Whitelist tokens (e.g., [RATING], [PHONE_NUMBER]) dengan masking/unmasking sederhana."""

from typing import Iterable, Tuple, Dict, Set
import re

DEFAULT_WHITELIST: Set[str] = {"[RATING]", "[PHONE_NUMBER]", "[EMAIL]", "[ADDRESS]", "[NIK]", "[URL]"}

def _build_mapping(whitelist: Iterable[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Bangun mapping token -> placeholder (Private Use Area) dan sebaliknya."""
    tokens = sorted(set(whitelist))
    base = 0xE000  
    fwd: Dict[str, str] = {}
    for i, tok in enumerate(tokens):
        fwd[tok] = chr(base + i)  
    rev = {v: k for k, v in fwd.items()}
    return fwd, rev

def mask_whitelist(x: str, whitelist: Iterable[str] = DEFAULT_WHITELIST) -> str:
    """Ganti token whitelist dengan placeholder aman agar tak tersentuh fungsi berikutnya."""
    if not isinstance(x, str):
        return x
    fwd, _ = _build_mapping(whitelist)
    if not fwd:
        return x
    pat = re.compile("|".join(re.escape(t) for t in fwd.keys()))
    return pat.sub(lambda m: fwd[m.group(0)], x)

def unmask_whitelist(x: str, whitelist: Iterable[str] = DEFAULT_WHITELIST) -> str:
    """Pulihkan placeholder menjadi token whitelist semula."""
    if not isinstance(x, str):
        return x
    _, rev = _build_mapping(whitelist)
    if not rev:
        return x
    pat = re.compile("|".join(re.escape(p) for p in rev.keys()))
    return pat.sub(lambda m: rev[m.group(0)], x)

# Back-compat alias
def protect_whitelist(x: str, whitelist: Iterable[str] = DEFAULT_WHITELIST) -> str:
    return mask_whitelist(x, whitelist)
