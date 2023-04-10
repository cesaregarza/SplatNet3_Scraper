# Contributing to the project

Thank you for your interest in contributing to this project! This document will provide you with information on how to contribute to the project, including how to report bugs, request features, code style and standards, and more. If you have any questions, feel free to open an issue or contact me on Discord (Joy#2406).

## Table of Contents

- [Reporting bugs](#reporting-bugs)
- [Requesting features](#requesting-features)
- [Code style and standards](#code-style-and-standards)
- [Setting up your development environment](#setting-up-your-development-environment)
- [Submitting pull requests](#submitting-pull-requests)
- [Contacting me](#contacting-me)

## Reporting bugs

If you find a bug in the project, please open an issue on the GitHub repository. Please include the following information in your issue:

- The version of the project you are using
- The version of Python you are using
- The operating system you are using
- A description of the bug
- If possible, a code snippet that reproduces the bug
- If possible, a traceback of the bug

Please make sure to remove any sensitive information from your code snippet and traceback before posting them, such as your session token, gtoken, and bullet token. If you are unsure of how to remove sensitive information from your code snippet and traceback, please contact me on Discord (Joy#2406).

## Requesting features

Feature requests are welcome, but bear in mind that I may reject your feature request if I do not think it is a good fit for the project. The scope of the project is narrow, any feature requests that require additional libraries or dependencies will be rejected without further consideration. This includes but is not limited to: CLIs, GUIs, web applications, computer vision, and integration with other services. Knowing this, please open an issue on the GitHub repository if you have a feature request. Please include the following information in your issue:

- A description of the feature
- Why you think this feature is a good fit for the project
- If possible, a code snippet that demonstrates how the feature would work
- If possible, an example of another project that has a similar feature

Before creating a new issue, please make sure to search the existing issues to avoid duplicates. If you find an issue that is similar to the bug you encountered or the feature you want to request, feel free to comment on that issue with additional information or suggestions. This helps me keep the issue tracker organized and makes it easier to address issues more efficiently.

If you are unsure of whether your feature request is a good fit for the project, just open an issue and I will let you know.

## Code style and standards

I want to preface this section by saying that if you are unsure about any of the code style and standards listed below, please **open your pull request anyway** and I will let you know or guide you through the process. I am not trying to be difficult, but I truly believe in the broken windows theory of code and want to ensure that the codebase remains in the best shape possible.

This project follows the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for the most part with a single exception: line length. The maximum line length is 80 characters instead of 79 characters. This is opinionated, and I will not accept pull requests that change the line length. The easiest way to conform to this style guide is to use an auto-formatter. The recommended auto-formatters are [Black](https://github.com/psf/black) and [isort](https://github.com/PyCQA/isort). Code that does not conform to the style guide will not be accepted, this includes code that does not pass [flake8](https://github.com/PyCQA/flake8)'s linting.

All new code must be type hinted. This project uses [mypy](http://mypy-lang.org/) for static type checking, and all code must pass mypy's type checking. There are very few exceptions to this rule, and you need to have a very good reason for using # type: ignore.

No pull requests will be accepted that do not have unit tests. This project uses [pytest](https://docs.pytest.org/en/latest/) for unit testing.

This project uses [Sphinx](https://www.sphinx-doc.org/en/master/) for documentation. Please make sure to document your code using docstrings and type hints.

## Setting up your development environment

To set up the development environment for this project, you will need to install [Python 3.10](https://www.python.org/downloads/) or higher. It is heavily recommended to use [pyenv](https://github.com/pyenv/pyenv) for managing Python versions, although it's optional. You will also need to install [Poetry](https://python-poetry.org/). Once you have installed Python and Poetry, follow these steps to set up the development environment:

1. Clone the repository:

    ```bash
    git clone https://github.com/cesaregarza/SplatNet3_Scraper.git
    ```

2. Change into the project directory:

    ```bash
    cd SplatNet3_Scraper
    ```

3. (Optional) Install the correct version of Python using pyenv:

    ```bash
    pyenv install 3.10.9
    pyenv virtualenv 3.10.9 splatnet3-scraper
    pyenv local splatnet3-scraper
    pyenv activate splatnet3-scraper
    ```

4. Install the dependencies:

    ```bash
    poetry install
    ```

Now you're ready to make changes to the codebase. Be sure to follow the code style and standards mentioned in the previous section. When you're done with your changes, don't forget to run the tests and check for type hinting and style issues using `pytest`, `mypy`, and `flake8` as described in the "Code style and standards" section.

## Submitting pull requests

If you would like to contribute to the project, please open a pull request on the GitHub repository. Please make sure to follow the code style and standards listed above. If you are unsure of how to do this, please open your pull request anyway and I will let you know or guide you through the process. If you are new to programming, please do not be discouraged from contributing to the project. I am happy to help you get started and answer any questions you may have.

## Contacting me

If you have any questions, feel free to open an issue or contact me on Discord (Joy#2406). I am happy to help you get started and answer any questions you may have, but I may not be able to respond immediately.
