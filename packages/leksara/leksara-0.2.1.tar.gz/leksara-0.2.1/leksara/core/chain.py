"""ReviewChain runner and pipeline executor.

Fitur utama:
1. Eksekusi berurutan: patterns -> functions.
2. Setiap step boleh berupa callable langsung atau tuple (callable, {kwargs}).
3. Bisa dipakai fungsional (``run_pipeline`` / ``leksara``) atau OOP (``ReviewChain``).
4. Opsi benchmark=True mengembalikan metrik waktu per step & total.

Contoh cepat:
    from leksara.core.chain import run_pipeline
    from leksara.functions.cleaner.basic import case_normal, remove_punctuation
    data = ["Halo GAN!!!", "Produk BAGUS???"]
    pipe = {"patterns": [], "functions": [case_normal, remove_punctuation]}
    cleaned = run_pipeline(data, pipe)

Catatan: Default pipeline (jika None) menggunakan subset fungsi dasar
yang tersedia (remove_tags -> case_normal -> remove_whitespace) bila dapat diimpor.
"""

# ReviewChain runner dan executor pipeline
from __future__ import annotations

from typing import Callable, Iterable, Dict, Any, Union, Tuple, List, Optional
from dataclasses import dataclass
from time import perf_counter

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None  # type: ignore

# tambahkan import whitelist masker
from ..utils.whitelist import mask_whitelist, unmask_whitelist
from ..functions.review.advanced import mask_rating_tokens, unmask_rating_tokens, replace_rating
from .presets import get_preset as _get_preset

TextFn = Callable[[str], str]
Step = Union[TextFn, Tuple[TextFn, Dict[str, Any]]]


# ---------------------------- utils ----------------------------
def _normalize_steps(steps: Optional[Iterable[Step]]) -> List[TextFn]:
    """Konversi step menjadi callable murni, simpan nama step utk pelaporan."""
    out: List[TextFn] = []
    if not steps:
        return out
    for s in steps:
        if callable(s):
            fn = s
            setattr(fn, "__leksara_name__", getattr(fn, "__name__", repr(fn)))
            setattr(fn, "__leksara_original__", fn)
            out.append(fn)
        elif isinstance(s, tuple) and len(s) == 2 and callable(s[0]) and isinstance(s[1], dict):
            fn, kwargs = s
            name = getattr(fn, "__name__", repr(fn))
            def wrapped(x: str, _fn=fn, _kw=kwargs):
                return _fn(x, **_kw)
            setattr(wrapped, "__leksara_name__", name)
            setattr(wrapped, "__leksara_original__", fn)
            out.append(wrapped)
        else:
            raise TypeError("Step pipeline harus callable atau (callable, dict kwargs).")
    return out


def _wrap_with_rating_mask(fn: TextFn) -> TextFn:
    """Bungkus fungsi agar rating yang dihasilkan langsung dimasking."""
    name = getattr(fn, "__leksara_name__", getattr(fn, "__name__", repr(fn)))
    original = getattr(fn, "__leksara_original__", fn)

    def wrapped(x: str, _fn=fn):
        result = _fn(x)
        return mask_rating_tokens(result)

    setattr(wrapped, "__leksara_name__", name)
    setattr(wrapped, "__leksara_original__", original)
    return wrapped


def _prepare_functions(steps: Optional[Iterable[Step]]) -> List[TextFn]:
    functions = _normalize_steps(steps)
    prepared: List[TextFn] = []
    for fn in functions:
        original = getattr(fn, "__leksara_original__", fn)
        if original in (mask_rating_tokens, unmask_rating_tokens):
            prepared.append(fn)
            continue
        if original is replace_rating:
            prepared.append(_wrap_with_rating_mask(fn))
            continue
        prepared.append(fn)
    return prepared


def _compose(funcs: Iterable[TextFn]) -> TextFn:
    funcs = list(funcs)
    def _f(x: str) -> str:
        y = x
        for fn in funcs:
            y = fn(y)
            if not isinstance(y, str):
                name = getattr(fn, "__leksara_name__", getattr(fn, "__name__", repr(fn)))
                raise TypeError(f"Step '{name}' returned {type(y).__name__}, expected str")
        return y
    return _f

# cleaner subpackage
def _default_pipeline() -> Dict[str, List[Step]]:
    """Pipeline default sederhana bila user tak memberi pipeline."""
    patterns: List[Step] = []
    functions: List[Step] = []
    try:
        from ..functions.cleaner.basic import remove_tags, case_normal, remove_whitespace, remove_punctuation, remove_emoji  # type: ignore
        functions.extend([remove_tags, case_normal, remove_emoji, remove_punctuation, remove_whitespace])
    except Exception:
        # jika fungsi dasar belum tersedia, pakai pipeline kosong
        pass
    return {"patterns": patterns, "functions": functions}

# ------------------------ functional API -----------------------
def leksara(
    data,  # pd.Series | Iterable[str]
    pipeline: Optional[Dict[str, Iterable[Step]]] = None,
    *,
    benchmark: bool = False,
    preset: Optional[str] = None,
):
    """Eksekusi pipeline: patterns → functions.

    Args:
        data: pd.Series atau iterable of str
        pipeline: {"patterns": [...], "functions": [...]} (optional)
        preset: nama preset (mis. "ecommerce_review") sebagai sugar untuk pipeline
        benchmark: jika True kembalikan (hasil, metrics)
    """
    # Pilih salah satu: preset atau pipeline
    if preset is not None:
        if pipeline is not None:
            raise ValueError("Gunakan salah satu: preset atau pipeline, bukan keduanya.")
        pipeline = _get_preset(preset)

    if pipeline is None:
        pipeline = _default_pipeline()

    # Langkah-langkah pipeline (patterns dan functions)
    patterns = _normalize_steps(pipeline.get("patterns", []))
    functions = _prepare_functions(pipeline.get("functions", []))

    # Susun urutan langkah. Proteksi whitelist hanya jika ada functions.
    steps_all = [*patterns]
    if functions:
        steps_all += [mask_whitelist, *functions, unmask_whitelist, unmask_rating_tokens]

    # Timing agregat per step
    timings_map: Dict[str, float] = {}

    def _run_steps_with_timing(x: str) -> str:
        y = x
        for step in steps_all:
            if not benchmark:
                y = step(y)
            else:
                t0 = perf_counter()
                y = step(y)
                dt = perf_counter() - t0
                name = getattr(step, "__leksara_name__", getattr(step, "__name__", repr(step)))
                timings_map[name] = timings_map.get(name, 0.0) + dt
        return y

    # Mendukung iterable biasa dan pandas Series
    if pd is not None and isinstance(data, pd.Series):
        out = data.apply(lambda v: _run_steps_with_timing(v) if isinstance(v, str) else v)
    else:
        out = [_run_steps_with_timing(v) if isinstance(v, str) else v for v in data]

    if benchmark:
        total = sum(timings_map.values())
        metrics = {
            "n_steps": len(steps_all),
            "total_time_sec": total,
            "per_step": sorted(timings_map.items(), key=lambda kv: kv[1], reverse=True),
        }
        return out, metrics
    return out


def run_pipeline(
    data,
    pipeline: Optional[Dict[str, Iterable[Step]]] = None,
    *,
    benchmark: bool = False,
    preset: Optional[str] = None,
):
    return leksara(data, pipeline=pipeline, benchmark=benchmark, preset=preset)


# -------------------------- OOP API ----------------------------
@dataclass
class ReviewChain:
    """
    Pipeline OOP sederhana:
    - Dapat dibangun dari steps sekuensial (callable atau (callable, {kwargs}))
    - Kompatibel dgn API lama via from_steps(patterns=..., functions=...) → akan menyisipkan mask_whitelist/unmask_whitelist
    - Menyediakan fit/transform/fit_transform, process_text, run_on_series, named_steps
    """

    def __init__(self, steps: Optional[Iterable[Step]] = None):
        self.steps: List[Step] = list(steps or [])

    @classmethod
    def from_steps(
        cls,
        *,
        patterns: Optional[Iterable[Step]] = None,
        functions: Optional[Iterable[Step]] = None,
    ) -> "ReviewChain":
        # kompat lama: jika keduanya None, pakai default pipeline
        if patterns is None and functions is None:
            pipe = _default_pipeline()
            patterns = pipe["patterns"]
            functions = pipe["functions"]

        seq: List[Step] = []
        # Patterns jalan dulu (apa adanya)
        if patterns:
            seq.extend(list(patterns))
        # Sisipkan proteksi whitelist di antara patterns → functions
        if functions:
            prepared = _prepare_functions(functions)
            seq.append(mask_whitelist)           # Mask token whitelist
            seq.extend(prepared)                 # Jalankan functions (dengan proteksi rating)
            seq.append(unmask_whitelist)         # Kembalikan token whitelist
            seq.append(unmask_rating_tokens)     # Pulihkan titik desimal rating

        return cls(seq)

    @classmethod
    def from_preset(cls, name: str) -> "ReviewChain":
        """Bangun ReviewChain langsung dari nama preset."""
        steps = _get_preset(name)
        return cls.from_steps(patterns=steps.get("patterns"), functions=steps.get("functions"))

    def __repr__(self) -> str:
        return f"ReviewChain(steps={self.named_steps})"

    def __str__(self) -> str:
        return self.__repr__()

    def _build_callable(self) -> TextFn:
        return _compose(_normalize_steps(self.steps))

    @property
    def named_steps(self) -> Dict[str, str]:
        """Dict: step_i -> nama fungsi (untuk inspeksi cepat)."""
        fns = _normalize_steps(self.steps)
        return {
            f"step_{i}": getattr(fn, "__leksara_name__", getattr(fn, "__name__", repr(fn)))
            for i, fn in enumerate(fns)
        }

    def fit(self, data=None, y=None):  # stateless
        return self

    def transform(self, data, *, benchmark: bool = False):
        fns = _normalize_steps(self.steps)

        timings_map: Dict[str, float] = {}

        def run_one(x: str) -> str:
            y = x
            for fn in fns:
                if not benchmark:
                    y = fn(y)
                else:
                    t0 = perf_counter()
                    y = fn(y)
                    dt = perf_counter() - t0
                    name = getattr(fn, "__leksara_name__", getattr(fn, "__name__", repr(fn)))
                    timings_map[name] = timings_map.get(name, 0.0) + dt
            return y

        if isinstance(data, str):
            out = run_one(data)
        elif pd is not None and isinstance(data, pd.Series):
            out = data.apply(lambda v: run_one(v) if isinstance(v, str) else v)
        else:
            out = [run_one(v) if isinstance(v, str) else v for v in data]

        if benchmark:
            total = sum(timings_map.values())
            metrics = {
                "n_steps": len(fns),
                "total_time_sec": total,
                "per_step": sorted(timings_map.items(), key=lambda kv: kv[1], reverse=True),
            }
            return out, metrics
        return out

    def fit_transform(self, data, y=None, *, benchmark: bool = False):
        self.fit(data, y)
        return self.transform(data, benchmark=benchmark)

    # ----- API lama (kompat) -----
    def process_text(self, text: str) -> str:
        return self._build_callable()(text)

    def run_on_series(self, series, *, benchmark: bool = False):
        return self.transform(series, benchmark=benchmark)
