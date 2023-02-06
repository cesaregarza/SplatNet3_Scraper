# SplatNet 3 Scraper

[![Tests Status](./reports/junit/tests-badge.svg?dummy=8484744)](https://htmlpreview.github.io/?https://github.com/cesaregarza/SplatNet3_Scraper/blob/main/reports/junit/report.html) ![Coverage Status](./reports/coverage/coverage-badge.svg?dummy=8484744) ![Flake8 Status](./reports/flake8/flake8-badge.svg?dummy=8484744) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**SplatNet 3 Scraper** is a Python library for scraping data from the Splatoon 3 SplatNet 3 API. It is designed to be as lightweight as possible, with minimal dependencies to make it easy to integrate into other projects.

**SplatNet 3 Scraper** started as a fork of **[s3s](https://github.com/frozenpandaman/s3s)**, but has since been rewritten from scratch while incorporating much of the login flow logic of s3s. As a result, I am deeply indebted to the authors of s3s for their work. This project would not have been possible without their efforts.

## Features

* Lightweight and minimal dependencies. Only requires the `requests` library. Requires Python 3.10 or later.
* The `scraper` module provides a high level API that enables a quick and easy way to get data from the SplatNet 3 API, only requiring the user to provide their session token.
* The `base` module provides a low level API that allows for more fine-grained control over the scraping process. It is designed to be used by the scraper module, but is designed to be flexible enough to be used by other projects as well.
* Configuration file support is compatible with the configuration file format used by `s3s`.
* Responses from the SplatNet 3 API can be saved and loaded from disk, currently supporting the following formats:
  * JSON
  * gzip-compressed JSON
  * csv
  * parquet (by installing `splatnet3_scraper[parquet]` or the `pyarrow` library)

## Installation

**SplatNet3_Scraper** is currently under active development and is not yet available on PyPI. No wheels are currently available. If you would like to use this early version, you can install it from source by cloning this repository and running `pip install .` in the root directory.

## Usage

There are two ways to use **SplatNet3_Scraper**. The first is to use the `scraper` module, which provides a high level API that greatly simplifies the process of retrieving data from SplatNet 3. The second is to use the `base` module, which provides a low level API that allows for much more fine-grained control over the scraping process. Either way, both modules require a session token to be provided.

### Using the `scraper` module

The `scraper` module is a batteries-included module that allows queries to be made to the SplatNet 3 API with minimal effort. It is designed to be used by the end user, and as such it is the easiest and recommended way to get started with **SplatNet3_Scraper**. The `scraper` module provides the `SplatNet3_Scraper` class, which is used to make queries to the SplatNet 3 API. The `SplatNet3_Scraper` class can be instantiated in one of a few ways: by providing a session token, by providing the path to a configuration file, or by loading environment variables.

#### Instantiating the `SplatNet3_Scraper` class by providing a session token

```python
from splatnet3_scraper import SplatNet3_Scraper
scraper =SplatNet3_Scraper.from_session_token("session_token")
scraper.query("StageScheduleQuery")
```

#### Instantiating the `SplatNet3_Scraper` class by providing the path to a configuration file

```python
from splatnet3_scraper import SplatNet3_Scraper
scraper = SplatNet3_Scraper.from_config_file(".splatnet3_scraper")
scraper.query("StageScheduleQuery")
```

#### Instantiating the `SplatNet3_Scraper` class by loading environment variables

The following environment variables are supported:

* `SN3S_SESSION_TOKEN`
* `SN3S_GTOKEN`
* `SN3S_BULLET_TOKEN`

```python
from splatnet3_scraper import SplatNet3_Scraper
scraper = SplatNet3_Scraper.from_env()
scraper.query("StageScheduleQuery")
```

#### Querying the SplatNet 3 API

The `SplatNet3_Scraper` class provides a `query` method that can be used to make queries to the SplatNet 3 API. The `query` method takes a single argument, which is the name of the query to make. The `query` method returns a `QueryResponse` object, which contains the response data from the SplatNet 3 API. The `QueryResponse` object provides a `data` property that can be used to access the response data. The `QueryResponse` module also supports numpy-style indexing, which can be used to quickly and clearly access specific parts of the response data. For example, the following code will print the game mode name of the the current stage rotation schedule:

```python
from splatnet3_scraper import SplatNet3_Scraper
scraper = SplatNet3_Scraper.from_env()
response = scraper.query("StageScheduleQuery")
print(response["xSchedules", "nodes", 0, "vsRule", "name"])
```

#### Saving and loading responses

The `QueryResponse` class provides a `parsed_json` method that can be used to generate a `JSONParser` object from the response data. The `JSONParser` class provides multiple ways of interacting with the given data, including the ability to save the data to disk in a variety of formats. There are currently four different formats that are supported and can be used by passing the desired format to a `to_*` method such as `to_json`. The following formats are supported:

* JSON
* gzip-compressed JSON
* csv
* parquet (by installing `splatnet3_scraper[parquet]` or the `pyarrow` library)

Note: csv and parquet formats work by converting the response data from a nested dictionary to a columnar format. This is not recommended for single queries, but can be useful for interacting with large amounts of data as it deduplicates the JSON structure and allows for more efficient storage and querying.

The following code will save the response data to a file named `response.json` in the current directory:

```python
from splatnet3_scraper import SplatNet3_Scraper
scraper = SplatNet3_Scraper.from_env()
response = scraper.query("StageScheduleQuery")
response.parsed_json().to_json("response.json")
```

Additionally, the `JSONParser` class provides a `from_*` method that can be used to load data from a file. The following code will load the response data from the file `response.json` in the current directory:

```python
from splatnet3_scraper import JSONParser
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
| Full support for the SplatNet 3 API | :world_map: |
| Support for the SplatNet 2 API | :x: |
| Obtaining session tokens | :white_check_mark: |
| Full documentation | :world_map: |
| Full unit test coverage | :white_check_mark: |
| Columnar data format support | :construction: |
| CLI interface | :x: |
| Integration with stats.ink | :x: |
| PyPI package | :world_map: |
| Docker image | :world_map: |
| Executable binary | :x: |

## Docker Note

This project currently uses the standard library heavily, and as such it is not compatible with the `python:alpine` Docker image. I have no plans to change this. Use the `python:slim` image instead.

SplatNet3_Scraper is licensed under the GPLv3. See the LICENSE file for more details.
