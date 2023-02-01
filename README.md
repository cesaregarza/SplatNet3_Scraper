SplatNet 3 Scraper
==================
[![Tests Status](./reports/junit/junit-badge.svg?dummy=8484744)](./reports/junit/report.html)

**SplatNet 3 Scraper** is a Python library for scraping data from the Splatoon 3 SplatNet 3 API. It is designed to be as lightweight as possible, with minimal dependencies to make it easy to integrate into other projects.

**SplatNet 3 Scraper** started as a fork of **[s3s](https://github.com/frozenpandaman/s3s)**, but has since been rewritten from scratch while incorporating much of the login flow logic of s3s. As a result, I am deeply indebted to the authors of s3s for their work. This project would not have been possible without their efforts.

Features
--------

* Lightweight and minimal dependencies. Only requires the `requests` library. Requires Python 3.10 or later.
* The `scraper` module provides a high level API that enables a quick and easy way to get data from the SplatNet 3 API, only requiring the user to provide their session token.
* The `base` module provides a low level API that allows for more fine-grained control over the scraping process. It is designed to be used by the scraper module, but is designed to be flexible enough to be used by other projects as well.
* Configuration file support is compatible with the configuration file format used by `s3s`.
* Responses from the SplatNet 3 API can be saved and loaded from disk, currently supporting the following formats:
  * JSON
  * gzip-compressed JSON
  * csv
  * parquet (by installing `splatnet3_scraper[parquet]` or the `pyarrow` library)

Installation
------------

**SplatNet3_Scraper** is currently under active development and is not yet available on PyPI. No wheels are currently available. If you would like to use this early version, you can install it from source by cloning this repository and running `pip install .` in the root directory.

Symbols
-------

| Symbol | Meaning |
| ------ | ------- |
| :white_check_mark: | Implemented |
| :construction: | In progress |
| :world_map: | Planned |
| :x: | Not planned |

Roadmap
-------

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

Docker Note
-----------

This project currently uses the standard library heavily, and as such it is not compatible with the `python:alpine` Docker image. I have no plans to change this. Use the `python:slim` image instead.

SplatNet3_Scraper is licensed under the GPLv3. See the LICENSE file for more details.
