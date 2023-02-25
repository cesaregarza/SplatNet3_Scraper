Contributing
============


Where to start?
---------------
All contributions, bug reports, bug fixes, documentation improvements,
enhancements, and ideas are welcome.

If you are brand-new to open-source development, splatnet3_scraper is a great
place to start.  It's a small project, well-documented, and has a friendly
community.  If you are looking for a place to start contributing, check out the
list of open issues.

If you are new to git, GitHub has a great guide on how to fork a repository and
make a pull request 
`here <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`_. 

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
* Files in root: These are the configuration files for the project.  These files
  are used to configure the project, such as the code quality, code coverage,
  and documentation.  These files will not end up in the final package, so they
  are not included in the distribution.  These are files that help the developer
  tools such as pytest work in the way that I want them to work.

