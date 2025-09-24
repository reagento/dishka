Contributing
***************************

``dishka`` is an opensource project and we are welcome the new developers to join us.

Getting started
========================

1. Clone project:

.. code-block::

    git clone git@github.com:reagento/dishka.git
    cd dishka

2. Create and activate virtual environment:

.. code-block::

    python3 -m venv .venv
    source .venv/bin/activate

3. Install development tools and project itself:

.. code-block::

    pip install -r requirements_dev.txt
    uv pip install -e .

Running linters
=====================

Currently we use ``ruff`` to check code. To run it do

.. code-block::

    ruff check

We do not use ruff formatter for all code, so ensure that you formatted only your part of code proposing new changes.
We have a lot of checks enabled and some of them can be false positive. Double check your code before suppressing any linter warning.

Running type checker
=====================

Currently we use ``mypy`` to check types. To run it do

.. code-block::

    mypy

Running tests
========================

Project contains several types of tests:

* unit tests of library itself
* integration with other libraries
* tests of example app.

All of them can be run using nox:

.. code-block::

    nox

You can run integration tests for all specified versions of library:

.. code-block::

    nox -t aiohttp


All integration tests are using specific versions of libraries by default. You can run them with latest version specifying it explicitly. E.g.:

.. code-block::

    nox -s aiohttp_latest

All requirement files for tests are located in ``/requirements`` dir

Building documentation
==============================

Documentation is created using sphinx. First of all you might need ``make`` installed on your system.
Then install documentation requirements:

.. code-block::

    pip install -r requirements_doc.txt

Compile docs:

.. code-block::

    sphinx-build -M html docs docs-build -W

Open file ``docs-build/html/index.html`` in your browser

Running security audit for GitHub Actions
==========================================

We use ``zizmor`` to audit our GitHub Actions workflows for security issues. To run it locally:

.. code-block::

    zizmor .github/workflows

Submitting changes
============================

We welcome new contributors, but we want to keep the library design as simple as possible, so new approaches may require some discussion. Here are some requirements:

1. Compatibility matters. If proposed changes introduce new parameters, they should not be required. Changes in behavior can be introduced under a toggle.
2. Bugfixes are always welcome.
3. New features should be discussed beforehand. They should not exceed the scope of the IoC container and should fit into the overall API design.
4. New integrations are never accepted into the library. You are free to publish them as a separate project.
5. New translations are accepted if we have at least three (3) maintainers who are eager to support them and can translate all documentation changes in a short period.

When submitting new pull request, ensure that you have run all tests and linters.
