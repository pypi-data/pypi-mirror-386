"""Public package exports with lazy loading to avoid heavy optional deps on import."""

from importlib import import_module

from .version import __version__

__all__ = [
    "leksara",
    "ReviewChain",
    "run_pipeline",
    "CartBoard",
    "get_preset",
    "setup_logging",
    "log_pipeline_step",
]

_CHAIN_EXPORTS = {"leksara", "ReviewChain", "run_pipeline"}
_LOGGING_EXPORTS = {"setup_logging", "log_pipeline_step"}
_PRESET_EXPORTS = {"get_preset"}
_FRAME_EXPORTS = {"CartBoard"}


def __getattr__(name):  # pragma: no cover - exercised implicitly during import
    if name in _CHAIN_EXPORTS:
        module = import_module("leksara.core.chain")
    elif name in _LOGGING_EXPORTS:
        module = import_module("leksara.core.logging")
    elif name in _PRESET_EXPORTS:
        module = import_module("leksara.core.presets")
    elif name in _FRAME_EXPORTS:
        module = import_module("leksara.frames.cartboard")
    else:
        raise AttributeError(f"module 'leksara' has no attribute '{name}'")

    value = getattr(module, name)
    globals()[name] = value  # cache for future access
    return value


def __dir__():  # pragma: no cover - simple helper
    return sorted(list(__all__) + list(globals().keys()))
