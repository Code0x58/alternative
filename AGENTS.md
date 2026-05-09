The repository defines testing via GitHub actions. When contributing:

* You must check the changes are correct using the same commands as the workflow:
  * `uv sync --dev`
  * `uv run --dev ruff format --check --diff .`
  * `uv run --dev ruff check .`
  * `uv run --dev pyrefly check .`
  * `uv run --dev mypy .`
  * `uv run --dev pytest -vv --cov=alternative --cov-report=xml --cov-fail-under=100 --junitxml=test-results.xml`
* Format code with `uv run --dev ruff format .` before committing.
* Any change to branching paths in `alternative.py` must be followed by a branch coverage run and review for material missing runtime coverage using `uv run --dev pytest --cov=alternative --cov-branch --cov-report=term-missing:skip-covered`.
* Name tests and functions in `snake_case` and give them triple-quoted docstrings similar to the current codebase.
