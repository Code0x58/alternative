Contributing and Releases
=========================

Start from a source checkout and read the repository's
`contribution instructions
<https://github.com/Code0x58/alternative/blob/master/AGENTS.md>`_.
See :doc:`quickstart` for library usage.

Validation
----------

The `CI workflow
<https://github.com/Code0x58/alternative/blob/master/.github/workflows/ci.yml>`_
is the source of truth for the supported test matrix, tool setup, and validation
commands. Follow its dependency-installation step, then run its formatting,
lint, type, stub, test, and documentation checks before submitting a change.
Dependency requirements live in ``pyproject.toml`` and ``uv.lock``; use the
checkout's configuration rather than a tool or dependency version copied from
this guide.

Keep user-facing behavior, examples, and API documentation in sync. The test
suite executes documentation code blocks and the complete tutorial package.
The documentation build must finish without warnings. Run the formatter before
committing, and follow the additional coverage and typing checks in the
contribution instructions when they apply.

When changing dependencies, update the project requirements and lockfile
together, then rerun validation. When changing packaging, also run the workflow's
distribution checks. Those checks install the built package outside the checkout
to verify what consumers receive.

.. _pycharm-typing-checks:

Typing Compatibility Checks
---------------------------

Keep the original typed call interface working when changing decorators or
registration. ``typing_tests/`` contains probes for supported calls and invalid
registrations; the CI workflow runs the command-line type checks.

For PyCharm-specific changes, run ``scripts/pycharm-type-probes.sh`` after setting
up the development environment. A clean run produces no output. Set
``PYCHARM_INSPECT_SH`` if the inspection command is not discovered automatically,
or ``PYCHARM_PYTHON`` to select the Python environment to inspect.

Known IDE diagnostics and related issue links are tracked in
``typing_tests/pycharm_xfails.json``. The check rejects unexpected diagnostics and
unexpected passes. When an IDE update fixes a case, remove its expected failure.
Keep the assertions active for other type checkers instead of adding call-site
suppressions.

Publishing
----------

After validation passes, publish a GitHub release for a version tag. The
`release workflow
<https://github.com/Code0x58/alternative/blob/master/.github/workflows/publish.yml>`_
defines the build and publication steps. It verifies the tag and package version,
checks the distributions, and publishes through the repository's configured
PyPI environment. Configure the publishing credentials and any required approval
rules there before releasing.
