Scraper Module
==============

The scraper module is the top-level interface provided by this library. It
provides a single class, :class:`SplatNet_Scraper`, which is used to scrape data
from the SplatNet 3 API. This class abstracts away the details of the API and
orchestrates multiple requests to the API to retrieve commonly-used data. This
is the interface best suited for most users, especially those who are not
especially familiar with Python or those who want to get started quickly.

All query methods of this class return a :class:`QueryResponse` object from the
:mod:`splatnet3_scraper.query` module. This object contains the response data
from the API as well as some metadata about the queries. For more information,
see the documentation for the :mod:`splatnet3_scraper.query` module.

Submodules
----------

.. python-apigen-entity-summary:: splatnet3_scraper.scraper.SplatNet_Scraper

.. python-apigen-entity-summary:: splatnet3_scraper.scraper.QueryMap