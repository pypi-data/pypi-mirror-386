# Contributing to Leksara

Thanks for your interest in improving Leksara. This guide outlines how to set up your environment, follow project conventions, validate changes, and submit pull requests that merge smoothly.

---

## Get set up

1. Fork the repository and clone your fork.
2. Create a feature branch named after the change scope (`feature/cartboard-flags`, `bugfix/pii-regex`, etc.).
3. Create and activate a virtual environment, then install development extras:

        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
        pip install --upgrade pip
        pip install -e .[dev]

4. Configure pre-commit hooks if you use them; otherwise run tooling manually (see below).

---

## Coding standards

- Follow the formatting enforced by `ruff` (configured in `pyproject.toml`). Run it with:

        ruff check leksara docs

- Add or preserve type hints wherever possible. Validate with:

        mypy leksara

- Write docstrings for public modules, classes, and functions. Keep documentation in sync with `docs/` content when behaviour changes.
- Avoid introducing non-ASCII characters unless they are part of test fixtures or resource content that already contains them.

---

## Testing strategy

- Run the full unit test suite before opening a pull request:

        pytest -q

- When working on a specific area, run targeted modules to shorten feedback cycles:

        pytest leksara/tests/test_cartboard_orchestrators.py
        pytest leksara/tests/test_patterns_pii.py

- Use coverage reports to ensure new logic is exercised:

        pytest --cov=leksara --cov-report=term-missing

- For performance-sensitive changes, combine unit tests with benchmarking utilities in `leksara.core.logging` or the optional `benchmark` extra.

---

## Documentation updates

- Every behavioural change should mention the update in the relevant Markdown file (`docs/features.md`, `docs/api.md`, `docs/examples.md`, etc.).
- Run the Markdown linter (GitHub Actions enforces the same rules) and resolve warnings locally:

        ruff format docs  # if using ruff formatter
        # or use markdownlint-cli if installed

- Keep examples runnable: code snippets must import available symbols and reflect the current public API.

---

## Pull request checklist

Before requesting a review:

- [ ] Tests pass locally (`pytest -q`).
- [ ] Static analysis checks are clean (`ruff`, `mypy`).
- [ ] Documentation reflects the change.
- [ ] Dependency additions (if any) are justified and documented in `docs/dependencies.md`.
- [ ] Commit history is concise and descriptive (squash fixup commits if necessary).

Provide context in the PR description: problem statement, solution overview, risk assessment, and manual verification steps.

---

## Reporting issues

If you encounter bugs or have enhancement ideas:

1. Search existing issues to avoid duplicates.
2. Include reproduction steps, Python version, OS details, and the preset/pipeline used.
3. Mention whether optional dependencies (emoji, Sastrawi) are installed—this often affects behaviour.

We appreciate detailed reports; they help triage quickly and keep the roadmap aligned with user needs.


