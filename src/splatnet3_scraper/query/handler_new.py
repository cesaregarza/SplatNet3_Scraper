from __future__ import annotations

import json
import logging

import requests

from splatnet3_scraper.auth import NSO
from splatnet3_scraper.auth.exceptions import SplatNetException
from splatnet3_scraper.auth.graph_ql_queries import queries
from splatnet3_scraper.auth.tokens import TokenManager, TokenManagerConstructor
from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.query.configuration.config import Config
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
        logging.info("Initialized QueryHandler")

    # @classmethod
    # def from_config_file(
    #     cls,
    #     config_path: str | None = None,
    # ) -> QueryHandler:
    #     """Creates a new instance of the class using a configuration file.

    #     If the user does not provide a configuration file path, the default path
    #     will be used, which is ``.splatnet3_scraper`` in the user's current
    #     working directory. The configuration file this method accepts is one
    #     that aligns with the standard configuration file format used by the
    #     standard library ``configparser`` module. The configuration file must
    #     have a ``[Tokens]`` section, which only requires the ``session_token``
    #     option to be set. The ``session_token`` option must be set to the user's
    #     session token. For a full list of all options that can be set in the
    #     config file, see the documentation for the ``Config`` class.

    #     Args:
    #         config_path (str | None): The path to the configuration file. If
    #             None, the default configuration file path of
    #             ``.splatnet3_scraper`` in the user's current working directory
    #             will be used. Defaults to None.

    #     Returns:
    #         QueryHandler: A new instance of the class using the configuration
    #             file provided, with all the options set in the configuration
    #             file.
    #     """
    #     config = Config.from_file(config_path)
    #     return cls(config.token_manager)
