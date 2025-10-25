# Installation Guide

This page covers supported environments, installation patterns, and checks you can run to confirm the toolkit works end-to-end.

---

## Supported environments

| Component | Versions tested in CI |
| --- | --- |
| Python | 3.9, 3.10, 3.11, 3.12 |
| Operating systems | Windows (PowerShell), macOS, Ubuntu |
| Pandas | ≥ 1.5 |

Leksara relies on pure-Python dependencies, so installation does not require a compiler on any supported platform.

---

## Quick install from PyPI

1. Create and activate a virtual environment (recommended for both local dev and CI):

    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

    For POSIX shells, run:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

2. Install the package:

    ```powershell
    pip install --upgrade pip
    pip install leksara
    ```

3. Verify the import:

    ```powershell
    python -c "from leksara import leksara; print(leksara(['tes'], preset='ecommerce_review'))"
    ```

The command should print a cleaned list without raising exceptions.

---

## Installing from source

Clone the repository and install in editable mode:

```powershell
git clone https://github.com/<org>/leksara.git
cd leksara
python -m venv .venv
\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e .
```

To run the full test suite and documentation linters:

```powershell
pip install -e .[dev]
pytest -q
```

Editable installs are recommended when contributing or when you need to customise bundled resources.

---

## Optional dependencies & extras

| Extra | Install command | Feature unlocked |
| --- | --- | --- |
| `emoji` | `pip install emoji>=2.0.0` | Improves emoji detection in `remove_emoji` and `CartBoard` noise analysis. |
| `regex` | `pip install regex>=2022.1.18` | Enables advanced regex features (named sets, possessive quantifiers) in PII detection. |
| `Sastrawi` | `pip install Sastrawi>=1.0.1` | Activates Indonesian stemming inside `word_normalization`. Without it the function returns input text unchanged. |
| `leksara[dev]` | `pip install leksara[dev]` | Installs linting and testing stack: `pytest`, `pytest-cov`, `ruff`, `mypy`, `mkdocs`. |

You can safely omit optional packages if corresponding features are not used in your pipeline. The library degrades gracefully and emits warnings when an optional dependency is missing.

---

## Resource files

Regex patterns and dictionaries are packaged with the wheel. When installing from source, ensure git submodules or data directories are present. Custom resource overrides should live outside the package directory to avoid merge conflicts; update loaders before invoking pipelines (see `docs/features.md`).

---

## Post-install verification

Run a smoke test to validate that PII masking, review normalisation, and benchmarking all work:

```python
from leksara import leksara
from leksara.frames.cartboard import get_flags

sample = ["Email saya test@example.com, rating 4/5!"]
cleaned, metrics = leksara(sample, preset="ecommerce_review", benchmark=True)
flags = get_flags(sample, merge_input=False)

assert "[EMAIL]" in cleaned[0]
assert metrics["n_steps"] > 0
assert bool(flags.loc[0, "pii_flag"]) is True
```

If the assertions pass, the critical pipelines and detection heuristics are operational.

---

## Troubleshooting

- **Virtual environment will not activate on Windows** – Run PowerShell as Administrator once and execute `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.
- **`ModuleNotFoundError: No module named 'Sastrawi'`** – Install `Sastrawi` or disable `word_normalization` in your pipeline; the library warns but continues when Sastrawi is missing.
- **Pandas `ImportError`** – Confirm that `pip install leksara` pulled the required pandas wheel for your Python version. If using conda, install pandas via conda first, then `pip install leksara`.
- **Corporate proxies / offline installs** – Pre-download the wheel using `pip download leksara -d ./dist` from a machine with internet access, then install via `pip install dist/leksara-<version>-py3-none-any.whl`.
- **Resource updates not taking effect** – Remember that many dictionaries are loaded when modules import. Restart your Python process or reload modules after editing resource files.


