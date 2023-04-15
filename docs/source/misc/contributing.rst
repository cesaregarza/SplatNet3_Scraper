============
Contributing
============

.. contents::
   :local:

Introduction
============

Where to start?
---------------
All contributions, bug reports, bug fixes, documentation improvements,
enhancements, and ideas are welcome.

If you are brand-new to open-source development, splatnet3_scraper is a great
place to start.  It's a small project, well-documented, and has a friendly
community.  If you are looking for a place to start contributing, check out the
`list of open issues <https://github.com/cesaregarza/SplatNet3_Scraper/issues>`_
.

If you are new to git, GitHub has a great guide on how to fork a repository and
make a pull request 
`here <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`_. 

Code of Conduct
---------------

splatnet3_scraper is committed to fostering a welcoming, inclusive, and
respectful community. We value the contributions of each individual and believe
that diverse perspectives can only strengthen the project. By participating in
this project, you agree to adhere to the following Code of Conduct.

Respect and inclusion:

* Treat others with kindness, empathy, and respect, regardless of their
  background, identity, or experience.
* Be open to constructive feedback and different opinions, while avoiding
  personal attacks.
* Foster a collaborative environment by offering assistance and being receptive
  to help from others.

Responsibility and professionalism:

* Act ethically and responsibly, ensuring that your actions do not harm others
  or the project.
* Maintain a professional demeanor in all communications, including issues, pull
  requests, and discussions.
* Resolve conflicts in a respectful and constructive manner, seeking the
  assistance of the maintainers if necessary.

Reporting and enforcement:

* If you witness or experience any behavior that goes against this Code of
  Conduct, report it to the maintainers immediately.
* The maintainers will take appropriate action, which may include warning or
  banning the offender from the project.
* Maintainers reserve the right to remove or modify any contributions that do
  not align with the project's values or this Code of Conduct.

By following these guidelines, we can create a positive and collaborative
environment that benefits all members of the splatnet3_scraper community.


Bug reports
-----------

Bug reports are vital to helping improve splatnet3_scraper. Having a thorough
bug report will help us understand your issue and resolve it as quickly as
possible for all users.

If you have found a bug, please report it in the issue tracker with a minimal
reproducible example.  If you are not sure if something is a bug, please ask in
the issue tracker. Bug reports must include:

.. WARNING::

    DO NOT POST ANY TOKENS. DO NOT POST ANY TOKENS.  DO NOT POST ANY TOKENS.
    Please redact any tokens from your code before posting it.

* A short, self-contained Python snippet reproducing the problem. You can use
  `gist <https://gist.github.com/>`_ to paste your code.
* The full traceback of the error.
* The version of Python you are using.
* The version of splatnet3_scraper you are using.
* Your operating system.
* A brief description of the problem.
* If possible, explain why this unexpected behavior is undesirable and what you
  expect instead.

Feature requests
----------------

Feature requests are welcome.  But take a moment to find out whether your idea
fits with the scope and aims of the project.  It's up to *you* to make a strong
case to convince the community of the merits of this feature.  Please provide as
much detail and context as possible, and remember that my time on this project
is, ultimately, limited.

The scope of this project is narrow.  It is intended to be a simple, lightweight
library for scraping data from the SplatNet 3 API. Any feature requests that
would require additional libraries or dependencies will require a very, very
strong justification to be considered for inclusion as an optional dependency.
Absolutely no libraries or dependencies will be considered for inclusion to the
core library. Additional features that are outside the scope of this project
include but are not limited to: a command-line interface, a GUI, a web
application, a web API implementation, computer vision, and integration with
other services such as ``stat.ink``. If you are interested in any of these
features, please consider creating a separate project.

Knowing this, if you still feel that your feature request is within the scope of
this project, please open an issue with the following:

* A description of the feature.
* A justification for why this feature belongs in splatnet3_scraper.
* If possible, a description of how you might go about implementing this
  feature or a link to a pull request that implements the feature.
* If possible, an example of another project that has implemented this feature
  and how it works.

If you are unsure of whether your feature request is within the scope of this
project, please open an issue and ask.  I am happy to discuss your ideas and
help you find a solution.

Contacting the maintainers
--------------------------

If you have any questions, feel free to open an issue or contact me on
Discord (Joy#2406). I am happy to help you get started and answer any questions
you may have, but I may not be able to respond immediately.

Working with the code
=====================

Getting started
---------------

To a new contributor, the splatnet3_scraper codebase may seem daunting at first.
The list of files in root and multiple directories may seem overwhelming
especially to someone who is new to open-source development.  But don't worry!
The codebase is actually quite simple and easy to understand.  Here is a
quick overview of the codebase:

* ``splatnet3_scraper``: The core library. This is where all the "meat" of the
  code is.  This is where the interfaces to the SplatNet 3 API are defined. This
  is where you'll spend most of your time if you are contributing to the
  library.
* ``tests``: The test suite.  This directory is where all the unit tests are
  defined.  If you are contributing to the library, you should add tests to this
  directory. If you are unsure how to write tests, feel free to still open your
  pull request and ask for help. I am happy to help you write tests or comment
  on how to improve your tests.
* ``docs``: The documentation.  This directory is where the documentation is
  defined.  Please note that not all documentation is written in this
  directory, most of the documentation is written in the docstrings of the
  code itself. If you are contributing to the library, you should add
  documentation to the docstrings of the code. If you are unsure how to write
  documentation, feel free to still open your pull request and ask for help.
  I am happy to help you write documentation or comment on how to improve your
  documentation. I also acknowledge that I am not the best at writing
  documentation, so if you have any suggestions on how to improve the
  documentation, please let me know.
* ``examples``: The examples.  This directory is where the examples are defined.
  This is where you can find examples of how to use the library.  If you are
  unsure how to contribute but know how to use the library, you can feel free
  to add an example to this directory. Examples do not need to be complex, do
  not need documentation, and do not need to be tested.  They are simply
  intended to show how to use the library.
* ``reports``: The reports.  This directory is where the reports are defined.
  This is where you can find reports of the code coverage and the code
  quality.  These reports are automatically generated by pytest-cov, but as I
  intend to use GitHub Actions in the future, these reports will likely be
  removed in the future.
* ``.github``: The GitHub configuration files. This directory contains
  configuration files and templates related to GitHub, such as issue
  templates, pull request templates, and GitHub Actions workflows. These files
  help maintain a consistent format for issues and pull requests, as well as
  automate certain tasks like testing and code coverage reporting. When
  contributing, please follow the templates provided for issues and pull
  requests to make it easier for the maintainers to review your contributions.
* Files in root: These are the configuration files for the project.  These files
  are used to configure the project, such as the code quality, code coverage,
  and documentation.  These files will not end up in the final package, so they
  are not included in the distribution.  These are files that help the developer
  tools such as pytest work in the way that I want them to work.

If you are still unsure of where to start, feel free to open an issue and ask
for help.  I am happy to help you get started.

Setting up your development environment
---------------------------------------

To set up your development environment, you will need to install the following
dependencies:

* Python 3.10 or later
* Poetry
* Git
* Pyenv (optional, but recommended)

To install Poetry, follow the
`official installation guide <https://python-poetry.org/docs/#installation>`_.

To install Pyenv, follow the
`official installation guide <https://github.com/pyenv/pyenv#installation>`_.
Pyenv is particularly useful for managing multiple Python versions on your
system.

Once you have installed Poetry and Pyenv, follow these steps to set up your
development environment:

1. Clone the repository:

   .. code-block:: bash

       $ git clone

2. Change into the repository directory:

   .. code-block:: bash

       $ cd splatnet3_scraper

3. (Optional) Install the correct Python version using pyenv:

   .. code-block:: bash

       $ pyenv install 3.10.9
       $ pyenv virtualenv 3.10.9 splatnet3_scraper
       $ pyenv local splatnet3_scraper

4. Install the dependencies:

   .. code-block:: bash

       $ poetry install

Now you are ready to start developing! To run the tests, run the following
command:

.. code-block:: bash

    $ poetry run pytest

To run the linter, run the following command:

.. code-block:: bash

    $ poetry run flake8 .

To run the type checker, run the following command:

.. code-block:: bash

    $ poetry run mypy .

To generate the documentation, run the following command:

.. code-block:: bash

    $ poetry run sphinx-build -b html docs docs/_build

Alternatively, you can use the ``Makefile`` to run these commands:

.. code-block:: bash

    $ make docs


Branching Strategy
------------------

This project uses
`GitFlow branching strategy <https://nvie.com/posts/a-successful-git-branching-model/>`_


Code style and standards
------------------------

I want to preface this section by saying that if you are unsure about any of the
code style and standards listed below, please open your pull request anyway and
I will let you know or guide you through the process.  I am not trying to be
difficult, but I truly believe in the broken windows theory of software and want
to ensure that the codebase remains in the best shape possible at all times.

This project follows the
`PEP 8 Style Guide for Python Code <https://www.python.org/dev/peps/pep-0008/>`_
for the most part with one major exception: line length. I prefer to use a line
length of 80 characters instead of 79 characters. This is opinionated and I will
not accept pull requests that change the line length. The easiest way to conform
to this style guide is to use an auto-formatter. The recommended auto-formatters
are `black <https://github.com/psf/black>`_ and
`isort <https://github.com/PyCQA/isort>`_. Code that does not conform to the
style guide will not be accepted, this includes code that does not pass
`flake8 <https://github.com/PyCQA/flake8>`_'s linting.

All new code but be type annotated.  This project uses
`mypy <https://mypy-lang.org/>`_ for static type checking, and all code must
pass mypy's type checking. There are very few exceptions to this rule; if you
believe a specific piece of code should not be type annotated, please open an
issue and we can discuss it. Be prepared to provide a compelling argument for
why ``# type: ignore`` should be used.

No pull requests will be accepted that do not have unit tests. This project uses
`pytest <https://docs.pytest.org/en/stable/>`_ for unit testing, and all code
must be tested. If you do not know how to write tests, please open a pull
request anyway and I will help you write tests.  I am happy to help you write
tests or comment on how to improve your tests.

All new code must be documented. This project uses the
`Google Style Python Docstrings <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_
for docstrings. This project uses
`Sphinx <https://www.sphinx-doc.org/en/master/>`_ for documentation, and all
code must be properly documented. Additionally, this project uses the flake8
plugin `darglint <https://github.com/terrencepreilly/darglint>`_ to ensure that
the docstrings are properly formatted. If you do not know how to write
documentation, please open a pull request anyway and I will help you write
documentation.  I am happy to help you write documentation or comment on how to
improve your documentation. It is important that the docstrings are properly
formatted, as this is how the documentation is generated.


Submitting a pull request
-------------------------

If you are unsure of how to submit a pull request, please follow these steps:

1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes.
4. Commit your changes.
5. Push your changes to your fork.
6. Repeat steps 3-5 until you are satisfied with your changes.
7. Open a pull request.

Make sure to follow the code style and standards listed above.  If you are
unsure about any of the code style and standards, please open your pull request
anyway and I will let you know or guide you through the process. If you are new
to programming, please do not be discouraged from contributing to the project.
I am happy to help you get started and answer any questions you may have, so
please do not hesitate to open an issue.


Review Process
--------------

All pull requests must be reviewed by at least one other contributor before
they can be merged. The reviewer will either approve the pull request, request
changes, or close the pull request. If the reviewer requests changes, the pull
request author must make the requested changes before the pull request can be
merged. If the reviewer closes the pull request, the pull request author may
reopen the pull request if they believe the pull request should be merged. If
the reviewer approves the pull request, the pull request will be merged.


Release Cycle
-------------

This project uses
`semantic versioning <https://semver.org/>`_ for versioning.  The release cycle
is as follows:

.. warning::

    This project is still in ``0.x.y`` development, so the release cycle is
    slightly different than the final release cycle.  The release cycle will
    change to the final release cycle once the project reaches ``1.0.0``.

Preliminary Release cycle
~~~~~~~~~~~~~~~~~~~~~~~~~

The preliminary release cycle will only be used until the project reaches
``1.0.0``.  The preliminary release cycle is as follows:

1. The ``main`` branch will be used for development.
2. Every time a new feature is added, the version number will be either bumped
   to the next minor version or the next patch version. Semantic versioning will
   mostly be followed, but with backwards-incompatible changes and significant
   enough features bumping the minor version rather than the major version. This
   is a modification of the semantic versioning specification only for the
   ``0.x.y`` development cycle.
3. Every time a new release is made, a new tag will be created with the version
   number as the tag name.

Final Release cycle
~~~~~~~~~~~~~~~~~~~

The final release cycle will be used once the project reaches ``1.0.0``.  The
final release cycle is as follows:

1. The ``main`` branch will be used for releases.
2. The ``develop`` branch will be used for development. Upon release of
   ``1.0.0``, the ``develop`` branch will be created from the ``main`` branch.
   No changes will be made to the ``main`` branch until the next release, in
   stark contrast to the preliminary release cycle.
3. Semantic versioning will be strictly followed.  Every time a new feature is
   added, the version number will be bumped to the next minor version or the
   next patch version in accordance with the semantic versioning specification.
   To be clear, the version number will be bumped to the next minor version if
   the new feature adds functionality in a backwards compatible manner.  The
   version number will be bumped to the next patch version for backwards
   compatible bug fixes.
4. Every time a new release is made, a new tag will be created with the version
   number as the tag name.
