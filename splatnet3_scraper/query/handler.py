import json

import requests

from splatnet3_scraper.auth import NSO, TokenManager
from splatnet3_scraper.auth.exceptions import SplatNetException
from splatnet3_scraper.auth.graph_ql_queries import queries
from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.query.config import Config
from splatnet3_scraper.query.responses import QueryResponse
from splatnet3_scraper.utils import retry


class SplatNet_QueryHandler:
    """This class implements all of the classes and functions defined in the
    splatnet3_scraper.auth module and can be seen as an example of how to put
    them together. While the class has a method to create the session token, a
    full implementation with a CLI is outside the scope of this project.
    """

    def __init__(self, config: Config) -> None:
        """Initializes the class, it is not meant to be instantiated directly,
        but rather through one of the available factory methods. Still, it can
        be instantiated directly if the user wants to use a custom Config class.

        Args:
            config (Config): The configuration to use.
        """
        self.config = config

    @staticmethod
    def from_config_file(
        config_file: str | None = None,
    ) -> "SplatNet_QueryHandler":
        """Creates a new instance of the class using a configuration file. If
        no configuration file is provided, the default configuration file,
        .splatnet3_scraper, will be used.

        Args:
            config_file (str | None): The path to the configuration file. If
                None, the default configuration file will be used. Defaults to
                None.

        Returns:
            SplatNet_QueryHandler: A new instance of the class.
        """
        config = Config(config_file)
        return SplatNet_QueryHandler(config)

    @staticmethod
    def generate_session_token_url(
        user_agent: str | None = None,
    ) -> tuple[str, bytes, bytes]:
        """Generates the URL to use to get the session token.

        Args:
            user_agent (str | None): The user agent to use. If None, the default
                user agent will be used. Defaults to None.

        Returns:
            tuple:
                str: The URL to use to get the session token.
                bytes: The state ID.
                bytes: The challenge solution.
        """
        nso = NSO.new_instance()
        url = nso.generate_login_url(user_agent)
        return url, nso.state, nso.verifier

    @staticmethod
    def from_session_token(session_token: str) -> "SplatNet_QueryHandler":
        """Creates a new instance of the class using a session token.

        Args:
            session_token (str): The session token.

        Returns:
            SplatNet_QueryHandler: A new instance of the class.
        """
        token_manager = TokenManager.from_session_token(session_token)
        token_manager.generate_all_tokens()
        config = Config(token_manager=token_manager)
        return SplatNet_QueryHandler(config)

    @staticmethod
    def from_env() -> "SplatNet_QueryHandler":
        """Creates a new instance of the class using the environment
        variables.

        Returns:
            SplatNet_QueryHandler: A new instance of the class.
        """
        config = Config.from_env()
        return SplatNet_QueryHandler(config)

    @staticmethod
    def from_s3s_config(path: str) -> "SplatNet_QueryHandler":
        """Creates a new instance of the class using the s3s config file.

        Args:
            path (str): The path to the s3s config file.

        Returns:
            SplatNet_QueryHandler: A new instance of the class.
        """
        config = Config.from_s3s_config(path)
        return SplatNet_QueryHandler(config)

    def __query(
        self, query_name: str, variables: dict = {}
    ) -> requests.Response:
        """Internal method to query Splatnet 3, it does all of the heavy lifting
        and is used by the other methods to get the data.

        Args:
            query_name (str): The name of the query to use.
            variables (dict): The variables to use in the query. Defaults to {}.

        Returns:
            requests.Response: The response from the query.
        """
        return queries.query(
            query_name,
            self.config.get_token(TOKENS.BULLET_TOKEN),
            self.config.get_token(TOKENS.GTOKEN),
            self.config.get_data("language"),
            self.config.get("user_agent"),
            variables=variables,
        )

    # Repeat code, but I've elected to do this to make it easier to read
    def __query_hash(
        self, query_hash: str, variables: dict = {}
    ) -> requests.Response:
        """Internal method to query Splatnet 3, it does all of the heavy lifting
        and is used by the other methods to get the data.

        Args:
            query_hash (str): The hash of the query to use.
            variables (dict): The variables to use in the query. Defaults to {}.

        Returns:
            requests.Response: The response from the query.
        """
        return queries.query_hash(
            query_hash,
            self.config.get_token(TOKENS.BULLET_TOKEN),
            self.config.get_token(TOKENS.GTOKEN),
            self.config.get_data("language"),
            self.config.get("user_agent"),
            variables=variables,
        )

    # Repeat code, but I've elected to do this to make it easier to read
    @retry(times=1, exceptions=ConnectionError)
    def query_hash(
        self, query_hash: str, variables: dict = {}
    ) -> QueryResponse:
        """Given a query hash, it will query SplatNet 3 and return the response.

        Args:
            query_hash (str): The query hash to use.
            variables (dict): The variables to use in the query. Defaults to {}.

        Raises:
            SplatNetException: If the query was successful but returned at
                least one error.

        Returns:
            QueryResponse: The response from the query.
        """
        response = self.__query_hash(query_hash, variables)
        if response.status_code != 200:
            self.config.token_manager.generate_all_tokens()
            response = self.__query_hash(query_hash, variables)

        if "errors" in response.json():
            errors = response.json()["errors"]
            error_message = (
                "Query was successful but returned at least one error."
            )

            error_message += " Errors: " + json.dumps(errors, indent=4)
            raise SplatNetException(error_message)

        return QueryResponse(data=response.json()["data"])

    @retry(times=1, exceptions=ConnectionError)
    def query(self, query_name: str, variables: dict = {}) -> QueryResponse:
        """Queries Splatnet 3 and returns the data.

        Args:
            query_name (str): The name of the query to use.
            variables (dict): The variables to use in the query. Defaults to {}.

        Raises:
            SplatNetException: If the query was successful but returned at
                least one error.

        Returns:
            QueryResponse: The data from the query.
        """
        response = self.__query(query_name, variables)
        if response.status_code != 200:
            self.config.token_manager.generate_all_tokens()
            response = self.__query(query_name, variables)

        if "errors" in response.json():
            errors = response.json()["errors"]
            error_message = (
                "Query was successful but returned at least one error."
            )

            error_message += " Errors: " + json.dumps(errors, indent=4)
            raise SplatNetException(error_message)

        return QueryResponse(data=response.json()["data"])
