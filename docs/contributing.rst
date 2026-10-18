Contributing and Releases
=========================

Use uv 0.13.1 or newer. CI pins uv 0.13.1 and tests Python 3.10 through 3.15.
CI explicitly selects each interpreter so the local ``.python-version`` default
cannot override the matrix.
The committed ``uv.lock`` records development and documentation dependencies;
the package version is derived separately from Git tags by ``hatch-vcs``.
The editable package cache includes Git commits and tags so installed metadata
is refreshed when the version changes.

Validation
----------

Install the locked environment and run the same checks as CI:

.. code-block:: console

   $ uv sync --locked --dev --group=docs
   $ uv run --locked --dev ruff format --check --diff .
   $ uv run --locked --dev ruff check .
   $ uv run --locked --dev pyrefly check .
   $ uv run --locked --dev pyright typing_tests
   $ uv run --locked --dev mypy .
   $ uv run --locked --dev stubtest alternative
   $ uv run --locked --dev pytest --verbosity=2 --cov=alternative --cov-report=xml --cov-fail-under=100 --junit-xml=test-results.xml
   $ uv run --locked --group=docs sphinx-build --fail-on-warning --keep-going --builder=html docs /tmp/alternative-docs-html

Unset ``PYTEST_DISABLE_PLUGIN_AUTOLOAD`` before running pytest if your shell
defines it. Format changes with ``uv run --dev ruff format .`` before committing.
When changing dependencies, run ``uv lock --upgrade`` and commit the resulting
lockfile. The lockfile selects the newest compatible releases for each supported
Python version, including Sybil 9.3 on Python 3.10 and Sybil 10 on newer Python
versions. Run the full validation suite after upgrading, since lint and type
checker updates can require source and stub changes.
Dependabot proposes weekly dependency and GitHub Actions updates; actions are
pinned to full commit hashes.

Build and check both distribution formats before releasing:

.. code-block:: console

   $ uv build --no-build-isolation --python .venv/bin/python
   $ uv run --locked --dev python scripts/check_distributions.py dist

The build uses the installed, locked backend dependencies. The distribution
check installs the wheel in a fresh environment outside the checkout, exercises
the API and license metadata, then rebuilds the sdist and repeats the check.
The pytest suite also checks an external consumer with mypy, Pyright, and
Pyrefly against a fresh wheel installation. The package includes its stub and
``py.typed`` marker; the checkout is not added to these checkers' search paths.

Publishing
----------

Publish a GitHub release for a version tag such as ``v0.3.0``. The release workflow
runs the full validation matrix on that release commit, verifies that the tag
still identifies the commit, and checks that the built package version matches
the tag. Development and local version tags are rejected.

Validated distributions pass through an immutable workflow artifact to a separate
publishing job. Only that job receives ``id-token: write`` and access to the
``pypi`` environment. Configure PyPI Trusted Publishing for this repository's
``publish.yml`` workflow and ``pypi`` environment. Configure environment approval
rules in GitHub if releases require manual review. Active runs for the same
release tag are allowed to finish.
