QuickStart
==========

.. _installation:

Installation
------------

.. WARNING:: 
    This package is still in active development and does not have a stable API.
    The API may have breaking changes between minor versions until the 
    ``v1.0.0`` release, it is recommended to pin the version of this package to 
    a specific version.

To install the package, run the following command:

.. code-block:: bash

    pip install splatnet3_scraper

.. _usage:

Usage
-----

This package includes three interfaces for interacting with SplatNet 3. The
first is the :doc:`../api/scraper/scraper` module, which provides a user-level interface that
greatly simplifies the process of retrieving data from SplatNet 3. The second is
the :doc:`../api/query/query`, which provides a high-level interface that simplifies
the process of creating queries without having to worry about the underlying
implementation details. The third is the :doc:`../api/auth/auth` module, which provides a
low-level interface that gives the user full control over the authentication
and querying process. The :doc:`../api/scraper/scraper` module is recommended for most users,
it is the easiest to use and is designed with users who are not highly familiar
with Python or just do not want to worry about the implementation details. The
:doc:`../api/query/query` is recommended for users for whom the :doc:`../api/scraper/scraper` module
is not sufficient, but want to avoid having to worry about the implementation
details. The :doc:`../api/auth/auth` module is recommended for advanced users who want to
have full control over the authentication and querying process. All three
modules require a Nintendo Switch Online membership as well as having played at
least one match online in Splatoon 3. For more information on obtaining a
session token, see :doc:`session_token`.

.. _scraper_example:

Obtaining Ranked Battle Data
----------------------------

This example will show how to use the :doc:`../api/scraper/scraper` module to obtain ranked
battle data and save it to a JSON file. This is the recommended method for most 
users, as it is simple and handles query orchestration as well as their 
underlying implementation details automagically. This module provides a single
class, :class:`SplatNet_Scraper`, which contains many methods that can be used
to retrieve commonly requested data from SplatNet 3. This class is currently in
active development and as such the methods provided by this class are limited,
but more methods will be added as development continues. For a full list of
methods, see the documentation for :class:`SplatNet_Scraper`. If you need to
retrieve data that is not currently supported by this class, you can place a
feature request on the Github Repository as an issue, or you can use the
:doc:`../api/query/query` to create your own queries until the feature is added. First
we will import the :class:`SplatNet_Scraper` class and instantiate it using a
session token:

.. code-block:: python
    
    from splatnet3_scraper.scraper import SplatNet_Scraper
    session_token = "your_session_token"
    scraper = SplatNet_Scraper(session_token)

Please note that the ``session_token`` variable should be replaced with a valid
session token. That's all it takes to get started! The :class:`SplatNet_Scraper`
class is now ready to be used to retrieve data from SplatNet 3. Pulling data
from SplatNet 3 is as simple as calling one of the methods provided by the
:class:`SplatNet_Scraper` class. For this example, we will be using the
:func:`SplatNet_Scraper.get_vs_battles` method, which can be used to retrieve
data for all ranked battles. The following code can be used to retrieve ranked
battle data:

.. code-block:: python

    summary, battles = scraper.get_vs_battles(mode="anarchy", detail=True)

The ``summary`` variable is a :class:`QueryResponse` object, which contains the
data returned by the query as well as some metadata about the query. The
``data`` property can be used to access the raw data returned by the query. The
``battles`` variable is a list of :class:`QueryResponse` objects, which each
contain the data for a single ranked battle.

That's it, we now have the data we need. It's really that simple! This example
will keep being updated as the :class:`SplatNet_Scraper` class is updated, so
check back later for more examples or more features to be built-in to the
shown function, :func:`SplatNet_Scraper.get_vs_battles`.

.. _query_example:

Query Example
-------------

Let's say we want to access data not currently supported by the :doc:`../api/scraper/scraper`
module, such as the stage rotation schedule. We can use the :doc:`../api/query/query`
to create our own queries. The :doc:`../api/query/query` provides a high-level
interface that still abstracts away the implementation details, but gives the
user more control over the process. This module provides a main class, the
:class:`QueryHandler`, which can be used to create queries and execute them.

This example will show how to use the :doc:`../api/query/query` to obtain the stage
rotation schedule and save it to a JSON file. This is the recommended method for
users who want to pull data that is not currently supported by the
:doc:`../api/scraper/scraper` module, but do not want to worry about the implementation
details.


Obtaining and Saving the Stage Rotation Schedule
------------------------------------------------

This example will show how to use the ``query`` module to obtain
the stage rotation schedule and save it to a JSON file. This i
The ``scraper`` module is the recommended module for most users, as it provides
a high-level interface that greatly simplifies the process of retrieving data
from SplatNet 3. This module provides a single class, :class:`QueryHandler`, 
which can be used to retrieve data from SplatNet 3. There are a few ways to 
instantiate this class, but following in the spirit of the above example, we
will be using the :func:`QueryHandler.from_session_token` method, which takes a
session token as its only argument. For a full list of options, see the
documentation for :class:`QueryHandler`. First we will import the
:class:`QueryHandler` class and instantiate it using a session token:

.. code-block:: python

    from splatnet3_scraper.query import QueryHandler

    session_token = "your_session_token"
    handler = QueryHandler.from_session_token(session_token)

Please note that the ``session_token`` variable should be replaced with a valid
session token. Similar to the :doc:`../api/scraper/scraper` module, the ``handler`` object is
now ready to be used to retrieve data from SplatNet 3. The main way to retrieve
data from SplatNet 3 is by using the :func:`QueryHandler.query` method. This
method takes the query name as its first argument, and any variables that are
required by the query as its second argument. For a full list of queries and
their required variables, see the documentation for :doc:`queries`. For this
example, we will be using the ``StageScheduleQuery``, which requires no
variables to be passed. The following code can be used to retrieve the stage
rotation schedule for X Battles:

.. code-block:: python

    response = handler.query("StageScheduleQuery")

The ``response`` object is a :class:`QueryResponse` object, which contains the
data returned by the query as well as some metadata about the query. The
``data`` property can be used to access the raw data returned by the query. The
:class:`QueryResponse` object also supports numpy-style indexing, which can be
used to quickly and clearly access specific parts of the data. For example, the
following code can be used to access the name of the game mode for the first
X Battle in the schedule:

.. code-block:: python

    game_mode = response["xSchedules", "nodes", 0, "vsRule", "name"]

The :class:`QueryResponse` object also provides a
:func:`QueryResponse.parsed_json` method, which returns a :class:`JSONParser`
object that can be used to interact with the data in multiple ways. For more
information, see the documentation for :class:`JSONParser`. The following code
can be used to save the stage rotation schedule data to a JSON file:

.. code-block:: python

    response.parsed_json().to_json("schedule.json")

That's it! The stage rotation schedule data has now been saved to a JSON file.
You are now ready to start retrieving data from SplatNet 3!
