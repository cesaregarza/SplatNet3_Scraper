Auth Module
============

The auth module is a low-level interface to the SplatNet 3 API. It provides
three main classes and a helper class.

The :class:`NSO` class contains the logic for authenticating with Nintendo's
servers and obtaining the right access tokens. It generates the necessary
headers, bodies, and cookies for the requests to the SplatNet 3 API. It provides
methods to generate the ``gtoken`` and the ``bullet_token``. It also provides
the option to change the method that is used to generate the ``ftoken``. This
is useful if you wish to use a different method to generate the ``ftoken`` than
querying a third-party website running an emulated version of the Nintendo
Switch Online app.

The :class:`TokenManager` class provides an interface to store, retrieve, and
generate the tokens that are required to make requests to the SplatNet 3 API.
The :class:`Token` class is a helper class that is used by the
:class:`TokenManager` class to store the tokens alongside their ``token_type``.

The :class:`GraphQLQueries` class contains the GraphQL queries that are used
to query the SplatNet 3 API. It provides methods to generate the GraphQL query,
as well as a method to obtain the ``query_hash`` that is required to make the
request through a hashmap of the query names to their ``query_hash``.

For more information on the login process, see the :doc:`../../misc/login_flow`
page.

Submodules
----------

.. python-apigen-entity-summary:: splatnet3_scraper.auth.NSO

.. python-apigen-entity-summary:: splatnet3_scraper.auth.TokenManager

.. python-apigen-entity-summary:: splatnet3_scraper.auth.GraphQLQueries

.. python-apigen-entity-summary:: splatnet3_scraper.auth.Token