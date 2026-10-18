Contributing and Releases
=========================

Start from a source checkout with uv 0.13.1 or newer:

.. code-block:: console

   $ git clone https://github.com/Code0x58/alternative.git
   $ cd alternative

The commands below install the development tools, run the checks required for a
contribution, and build the documentation. See :doc:`quickstart` for library usage.

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

CI pins uv 0.13.1 and tests Python 3.10 through 3.15.
CI explicitly selects each interpreter so the local ``.python-version`` default
cannot override the matrix.
The committed ``uv.lock`` records development and documentation dependencies;
the package version is derived separately from Git tags by ``hatch-vcs``.
The editable package cache includes Git commits and tags so installed metadata
is refreshed when the version changes.

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

.. _typing-model:

Typing Model
------------

Wrapper types have the public parameter order ``Alternatives[S, P, R, Q]``
and ``Implementation[S, P, R, Q]``. ``R`` is the return type and ``Q`` is the
complete parameter list. For ordinary functions with a first positional
parameter, ``S`` is its type and ``P`` is the remaining parameter list; this split
also supports receiver binding for instance methods. Class and static method
wrappers use a private receiver marker and keep their callable signature in
``P`` and ``Q``.

For example, ``Alternatives[int, [str], str, [int, str]]`` describes a function
accepting an integer followed by a string and returning a string. This explicit
form is useful for wrapper annotations and typing probes; normal decorator use
relies on inference.

Name shared implementation and registration unions once. The stub's private
``@type_check_only`` base shares pytest decorator signatures without changing
runtime inheritance. Keep receiver-sensitive registration and descriptor types
on their owning classes; ``typing_tests/model_probes.py`` checks the public
``S, P, R, Q`` parameter order and both bound and unbound decorator APIs.

Alternatives retain positional overloads needed by PyCharm. Implementation
objects use their ParamSpec directly. The ParamSpec signatures preserve names,
defaults, keyword-only parameters, and arbitrary argument counts.

.. _pycharm-typing-checks:

PyCharm Typing Checks
---------------------

Run ``scripts/pycharm-type-probes.sh`` after syncing the development environment.
Set ``PYCHARM_INSPECT_SH`` if ``inspect.sh`` is outside the usual Toolbox location
and ``PYCHARM_PYTHON`` to use a different Python environment. The script copies
the package and probes into a temporary project, configures its Python SDK, and
requires a deliberately invalid control for every requested inspection. It leaves
the repository and your IDE settings untouched. A clean run produces no output;
exit status 1 reports unexpected diagnostics or passes, and status 2 means
inspection failed, was incomplete, or the xfail manifest was invalid.

The known PyCharm gaps in :doc:`api` are strict expected failures listed in
``typing_tests/pycharm_xfails.json``. Each entry identifies an assertion by its
expression, links a related JetBrains issue, and lists its exact diagnostics.
Formatting and line changes do not affect matching. A new diagnostic, including
one on an already affected assertion, fails the check. Missing expected
diagnostics produce ``XPASS`` failures; review and remove fixed expectations.
Use ``scripts/pycharm-type-probes.sh --show-xfails`` to display the known cases.
Do not add call-site type-checker suppressions or remove assertions to accommodate
an IDE gap.

The standalone ``typing_tests/pycharm_paramspec_repro.py`` reproduces callback
inference without importing this library. Related JetBrains reports cover
`ParamSpec matching outside Callable
<https://youtrack.jetbrains.com/issue/PY-77541>`_ and `decorated method binding
<https://youtrack.jetbrains.com/issue/PY-85027>`_. The separate
``PyNestedDecoratorsInspection`` false positive for decorators outside
``@classmethod`` or ``@staticmethod`` is excluded from the headless check.

.. _dispatch-implementation-notes:

Dispatch Implementation Notes
-----------------------------

The optimization recorded in :doc:`performance` keeps type-expression
construction and repeated binding off the normal call path. Runtime casts use
unevaluated type expressions, and ordinary calls invoke the selected callable
directly. Held bound alternatives bind the selected implementation on first use
and reuse it thereafter; registration remains open until that first use.
Bound views share registered metadata and resolve reference signatures only when
requested by introspection.
