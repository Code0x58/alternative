The repository defines testing via GitHub actions. When contributing:

* Run the same steps locally that the workflow performs. This includes running `uv run pytest`, `ruff format --check .`, `pyrefly check .`, and `mypy .`.
* Before running tests, install dependencies with `uv pip install --editable . --group dev`.
* Ensure code is formatted with `ruff format` before committing.
* Name tests and functions in `snake_case` and give them triple-quoted docstrings similar to the current codebase.
