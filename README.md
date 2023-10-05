# SplatNet 3 Scraper

[![Tests Status](./reports/junit/test-badge.svg?dummy=8484744)](https://htmlpreview.github.io/?https://github.com/cesaregarza/SplatNet3_Scraper/blob/main/reports/junit/report.html) ![Coverage Status](./reports/coverage/coverage-badge.svg?dummy=8484744) ![Flake8 Status](./reports/flake8/flake8-badge.svg?dummy=8484744) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**SplatNet 3 Scraper** is a Python library for scraping data from the Splatoon 3 SplatNet 3 API. It is designed to be as lightweight as possible, with minimal dependencies to make it easy to integrate into other projects.

**SplatNet 3 Scraper** started as a fork of **[s3s](https://github.com/frozenpandaman/s3s)**, but has since been rewritten from scratch while incorporating much of the login flow logic of s3s. As a result, I am deeply indebted to the authors of s3s for their work. This project would not have been possible without their efforts.

## Table of Contents

1. [Features](#features)
2. [Documentation](#documentation)
3. [Installation](#installation)
4. [Usage](#usage)
   - [Using the `scraper` module](#using-the-scraper-module)
   - [Using the `query` module](#using-the-query-module)
   - [Using the `auth` module](#using-the-auth-module)
5. [Roadmap](#roadmap)
6. [Contributing](#contributing)
7. [License](#license)

## Features

- Lightweight and minimal dependencies. Only requires the `requests` library. Requires Python 3.10 or later.
- The `scraper` module provides a user-level API that enables a quick and easy way to get data from the SplatNet 3 API, only requiring the user to provide their session token.
- The `query` module provides a high-level API that provides a simple way to make queries to the SplatNet 3 API. It automatically handles authentication and query handling, and provides a simple interface for accessing the response data.
- The `auth` module provides a low level API that allows for more fine-grained control over the scraping process. It greatly simplifies the process of authentication.
- Compatibility with the configuration file format used by `s3s`.
- Responses from the SplatNet 3 API can be saved and loaded from disk, currently supporting the following formats:
  - JSON
  - gzip-compressed JSON
  - csv
  - parquet (by installing `splatnet3_scraper[parquet]` or the `pyarrow` library)
- Heavily documented codebase, with extensive docstrings and type annotations for nearly all functions and classes. The documentation is also available on [Read the Docs](https://splatnet3-scraper.readthedocs.io/en/latest/index.html).

## Documentation

Detailed documentation for SplatNet 3 Scraper, including usage instructions, examples, and API reference, is available on Read the Docs:

[**SplatNet 3 Scraper Documentation**](https://splatnet3-scraper.readthedocs.io/en/latest/index.html)

We highly recommend referring to the documentation to get the most out of SplatNet 3 Scraper and understand its full capabilities.

## Installation

**SplatNet 3 Scraper** is currently under active development but is currently available on PyPI. It can be installed using pip:

```bash
pip install splatnet3_scraper
```

Note that the current versions of **SplatNet 3 Scraper** are currently `v0.x.y`, which means that the API is not guaranteed to be stable and may change at any moment. As such, it is highly recommended that you pin the version of **SplatNet 3 Scraper** that you are using until the API is stabilized with the release of `v1.0.0`.

## Usage

There are three ways to use **SplatNet 3 Scraper**. The first is to use the `scraper` module, which provides a top-level API that greatly simplifies the process of retrieving commonly requested data from SplatNet 3. This module is greatly recommended for most users. The second is to use the `query` module, which provides a high-level API that provides a simple interface to make queries to the SplatNet 3 API. This module is recommended for developers who can't find what they need with the `scraper` module. The third is to use the `auth` module, which provides a low-level API that gives the user the most control over the scraping process. This module is recommended for advanced developers who need to have full control over the authentication process. Whichever module you choose to use, all of them require providing a session token.

### Using the `scraper` module

The `scraper` module is by far the easiest way to get data from the SplatNet 3 API and the module that is recommended for most users, especially those who are not highly experienced with Python. The `scraper` module provides multiple functions that can be used to retrieve commonly requested data from the SplatNet 3 API. The `scraper` module is designed to be used by users who are not highly experienced with Python or users who do not need to have full control over the scraping process.

This module is currently under active development and is not yet complete. Please check back later for more functions.

### Using the `query` module

The `query` module is an easy-to-use module that enables fast and painless querying to the SplatNet 3 API. It handles authentication and query handling automagically, and provides a simple interface for accessing the response data. The `query` module is designed to be used by advanced users who need more control over the queries they make to the SplatNet 3 API. If you are looking for a simple way to get data from the SplatNet 3 API, you should use the `scraper` module instead.

The `query` module provides the `QueryHandler` class, which is used to make queries to the SplatNet 3 API. The `QueryHandler` class can be instantiated in one of a few ways: by providing a session token, by providing the path to a configuration file, or by loading environment variables.

### Using the `auth` module

:warning: **Warning: The `auth` module is intended for advanced users only. Most users should use the `scraper` or `query` modules for a simpler and more convenient experience.**

The `auth` module provides a low-level API that allows for more fine-grained control over the scraping process. It greatly simplifies the process of authentication and is designed for advanced developers who need full control over the authentication process.

To use the `auth` module, you will need to import the necessary components and handle the authentication flow manually. Please refer to the [documentation](https://splatnet3-scraper.readthedocs.io/en/latest/index.html) for detailed instructions and examples on how to use the `auth` module.

#### Instantiating the `QueryHandler` class by providing a session token

```python
from splatnet3_scraper.query import QueryHandler
handler = QueryHandler.from_session_token("session_token")
handler.query("StageScheduleQuery")
```

#### Instantiating the `QueryHandler` class by providing the path to a configuration file

```python
from splatnet3_scraper.query import QueryHandler
handler = QueryHandler.from_config_file(".splatnet3_scraper")
handler.query("StageScheduleQuery")
```

#### Instantiating the `QueryHandler` class by loading environment variables

The following environment variables are supported:

- `SN3S_SESSION_TOKEN`
- `SN3S_GTOKEN`
- `SN3S_BULLET_TOKEN`

```python
from splatnet3_scrape.query import QueryHandler
handler = QueryHandler.from_env()
handler.query("StageScheduleQuery")
```

#### Querying the SplatNet 3 API

The `QueryHandler` class provides a `query` method that can be used to make queries to the SplatNet 3 API. The `query` method takes a single argument, which is the name of the query to make. The `query` method returns a `QueryResponse` object, which contains the response data from the SplatNet 3 API. The `QueryResponse` object provides a `data` property that can be used to access the response data. The `QueryResponse` module also supports numpy-style indexing, which can be used to quickly and clearly access specific parts of the response data. For example, the following code will print the game mode name of the the current stage rotation schedule:

```python
from splatnet3_scraper.query import QueryHandler
handler = QueryHandler.from_env()
response = handler.query("StageScheduleQuery")
print(response["xSchedules", "nodes", 0, "vsRule", "name"])
```

#### Saving and loading responses

The `QueryResponse` class provides a `parsed_json` method that can be used to generate a `JSONParser` object from the response data. The `JSONParser` class provides multiple ways of interacting with the given data, including the ability to save the data to disk in a variety of formats. There are currently four different formats that are supported and can be used by passing the desired format to a `to_*` method such as `to_json`. The following formats are supported:

- JSON
- gzip-compressed JSON
- csv
- parquet (by installing `splatnet3_scraper[parquet]` or the `pyarrow` library)

Note: csv and parquet formats work by converting the response data from a nested dictionary to a columnar format. This is not recommended for single queries, but can be useful for interacting with large amounts of data as it deduplicates the JSON structure and allows for more efficient storage and querying.

The following code will save the response data to a file named `response.json` in the current directory:

```python
from splatnet3_scraper.query import QueryHandler
handler = QueryHandler.from_env()
response = handler.query("StageScheduleQuery")
response.parsed_json().to_json("response.json")
```

Additionally, the `JSONParser` class provides a `from_*` method that can be used to load data from a file. The following code will load the response data from the file `response.json` in the current directory:

```python
from splatnet3_scraper.query import JSONParser
parser = JSONParser.from_json("response.json")
```

## Symbols

| Symbol | Meaning |
| ------ | ------- |
| :white_check_mark: | Implemented |
| :construction: | In progress |
| :world_map: | Planned |
| :x: | Not planned |

## Roadmap

| Feature | Status |
| ------- | ------ |
| Support for the SplatNet 3 API | :white_check_mark: |
| Full support for the SplatNet 3 API | :white_check_mark: |
| Support for the SplatNet 2 API | :x: |
| Obtaining session tokens | :white_check_mark: |
| Full documentation | :white_check_mark: |
| Full unit test coverage | :white_check_mark: |
| Columnar data format support | :construction: |
| CLI interface | :x: |
| Integration with stat.ink | :x: |
| PyPI package | :white_check_mark: |
| Docker image | :world_map: |
| Executable binary | :x: |

## Contributing

We welcome contributions to SplatNet 3 Scraper! For detailed information on how to contribute, please refer to our [CONTRIBUTING.md](./CONTRIBUTING.md) file.

To report issues or request new features, please open an issue on the GitHub repository.

## License

SplatNet 3 Scraper is licensed under the GPLv3. See the [LICENSE](./LICENSE) file for more details.
