# Contributing

## Development setup

```bash
git clone https://github.com/ukw2d/addictune-sdk.git
cd addictune-sdk
uv sync --dev
```

## Running tests

```bash
uv run pytest tests/ -v
```

All tests must pass before merging. CI runs the full suite against Python 3.12, 3.13, and 3.14 on every push and pull request.

## Pull requests

- Keep changes focused — one concern per PR.
- Add or update tests for any changed behaviour.
- Run `uv run pytest tests/` locally before pushing.
- If you're adding a public API surface, update the README accordingly.

## Code style

Follow the conventions already present in the codebase:

- `async/await` throughout — no sync wrappers.
- Pydantic v2 models for all API responses.
- `logging.getLogger(__name__)` for log output — no handlers or formatters.
- No environment variables or `.env` files — configuration is explicit via `AddictuneConfig`.

## Reporting issues

Open a GitHub issue with:

- Python version and OS.
- Minimal reproduction steps.
- Expected vs. actual behaviour.

## License

By contributing you agree that your changes will be released under the [MIT License](LICENSE).
