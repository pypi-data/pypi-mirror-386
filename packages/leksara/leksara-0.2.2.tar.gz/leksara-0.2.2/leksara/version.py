"""Package version helper derived from installed metadata.

This file is kept minimal because the canonical version is provided by git tags via
``setuptools_scm``. When the project is built, the version is resolved from the
repository state and exposed here.
"""

from __future__ import annotations

try:
	from importlib.metadata import PackageNotFoundError, version
except ImportError:  # pragma: no cover - Python <3.8 compatibility shim
	from importlib_metadata import PackageNotFoundError, version  # type: ignore


def _get_version() -> str:
	try:
		return version("leksara")
	except PackageNotFoundError:
		return "0.0+unknown"


__version__ = _get_version()
