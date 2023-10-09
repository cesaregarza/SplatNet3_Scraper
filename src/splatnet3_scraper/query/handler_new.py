import json
import logging

import requests

from splatnet3_scraper.auth import NSO
from splatnet3_scraper.auth.exceptions import SplatNetException
from splatnet3_scraper.auth.graph_ql_queries import queries
from splatnet3_scraper.auth.tokens import TokenManager
from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.query.responses import QueryResponse
from splatnet3_scraper.utils import retry

logger = logging.getLogger(__name__)


class QueryHandler:
    """The QueryHandler class is the main class of the
    ``splatnet3_scraper.query`` module. It abstracts away the underlying
    implementation details of making queries to the SplatNet 3 API and makes it
    extremely easy to use. Token management is also handled by the QueryHandler
    so the user does not have to worry about having to regenerate tokens when
    they expire. The only exception to this is the session token, which the user
    must handle themselves as it is not possible to regenerate it automatically.
    The QueryHandler class is initialized with a Config class, which contains
    all the configuration options that the user can set. The QueryHandler class
    also contains multiple factory methods to create a new instance of the class
    to make it setting up the Config class much easier. The primary mode of
    operating the class is through the ``query`` method, which takes a query
    name and a dictionary of arguments and returns a QueryResponse object.
    """

    def __init__(self, token_manager: TokenManager) -> None:
        """Initializes a ``QueryHandler`` object.

        Args:
            token_manager (TokenManager): The ``TokenManager`` object to use to
                manage the tokens.
        """
        self._token_manager = token_manager
