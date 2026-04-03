# Contributing to `transformkit`

Thanks for your interest in improving the TransformKit Python SDK.

## Development

- **Python** 3.10+ — see `requires-python` in `pyproject.toml`.
- Create a venv: `python3 -m venv .venv && source .venv/bin/activate`
- Install in editable mode: `pip install -e . pytest pytest-asyncio`
- **Tests:** `pytest tests/ -v`
- **Lint:** `ruff check .` (install with `pip install ruff`)
- **Types:** `mypy src/` (install with `pip install mypy`)

## Code of conduct

Please read [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

## Pull requests

- Open a PR against the default branch with a short description of the change and the motivation.
- Add or update tests when behavior changes.
- Keep commits focused; we can squash on merge if needed.

## License

By contributing, you agree that your contributions are licensed under the **MIT License** (see [LICENSE](./LICENSE)).
