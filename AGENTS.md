The repository defines testing via GitHub actions. When contributing:

* You must check the changes are correct using the same commands as the workflow:
  * `uv sync --dev --group=docs`
  * `uv run --dev ruff format --check --diff .`
  * `uv run --dev ruff check .`
  * `uv run --dev pyrefly check .`
  * `uv run --dev mypy .`
  * `uv run --dev pytest --verbosity=2 --cov=alternative --cov-report=xml --cov-fail-under=100 --junit-xml=test-results.xml`
  * `uv run --group=docs sphinx-build --fail-on-warning --keep-going --builder=html docs /tmp/alternative-docs-html`
* Format code with `uv run --dev ruff format .` before committing.
* Keep the documentation in `docs/` up to date with user-facing behavior, API, and workflow changes. Documentation must compile without warnings.
* Keep `alternative.py` strictly typed: do not use `typing.Any` or `Any`, and do not add mypy or pyrefly suppression comments. Fix the annotations so public decorators remain transparent to type checkers and IDEs.
* Any change to branching paths in `alternative.py` must be followed by a branch coverage run and review for material missing runtime coverage using `uv run --dev pytest --cov=alternative --cov-branch --cov-report=term-missing:skip-covered`.
* Name tests and functions in `snake_case` and give them triple-quoted docstrings similar to the current codebase.
