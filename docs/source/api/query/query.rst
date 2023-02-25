Query Module
============

The query module is a high-level interface to the SplatNet 3 API. It provides
a simple interface for making queries to the API, and automatically handles
authentication, session management, and token refreshing.

The main class in this module is :class:`QueryHandler`, which is used to make
queries to the API. It is designed to be as easy to use as possible, and its
primary public method is :meth:`QueryHandler.query`, which takes a query string
and, if necessary, a dictionary containing query variables to pass to the API.
It returns a :class:`QueryResponse` object, which contains the response data
from the API as well as some metadata about the query. See the documentation
for :class:`QueryHandler` and :class:`QueryResponse` for more details.

Additionally, the :class:`JSONParser` class is provided for more advanced use
cases. It is not necessary to use this class directly, but it is provided for
those who wish to do so. As of version ``0.5.0``, this class is not being used
internally by any other class, and may be removed in a future version.

This module currently has no plans to support a CLI interface, and it is
intended to be used as a library for other projects.

Submodules
----------

.. python-apigen-entity-summary:: splatnet3_scraper.query.QueryHandler

.. python-apigen-entity-summary:: splatnet3_scraper.query.QueryResponse

.. python-apigen-entity-summary:: splatnet3_scraper.query.Config

.. python-apigen-entity-summary:: splatnet3_scraper.query.JSONParser