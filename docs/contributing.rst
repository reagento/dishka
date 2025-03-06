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



Running tests
========================

Project contains several types of tests:

* unit tests of library itself
* integration with other libraries
* tests of example app

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

    make html

Open file ``docs-build/html/index.html`` in your browser


Submitting changes
============================

We welcome new ideas and PRs but may request additional discussion if it affects internal structure or API.
When submitting new pull request, ensure that you have run all tests and linters.