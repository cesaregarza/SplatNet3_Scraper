import json
from typing import ParamSpec, TypeVar

import requests

from splatnet3_scraper.base.exceptions import SplatnetException
from splatnet3_scraper.base.graph_ql_queries import queries
from splatnet3_scraper.base.tokens import NSO, TokenManager
from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.scraper.config import Config
from splatnet3_scraper.scraper.responses import QueryResponse
from splatnet3_scraper.utils import retry

T = TypeVar("T")
P = ParamSpec("P")


class QueryMap:
    ANARCHY = "BankaraBattleHistoriesQuery"
    REGULAR = "RegularBattleHistoriesQuery"
    XBATTLE = "XBattleHistoriesQuery"
    PRIVATE = "PrivateBattleHistoriesQuery"
    LATEST = "LatestBattleHistoriesQuery"
    SALMON = "CoopHistoryQuery"
    CATALOG = "CatalogQuery"
    CHECKIN = "CheckinQuery"
    CHECKIN_QR = "CheckinWithQRCodeMutation"
    CONFIGURE_ANALYTICS = "ConfigureAnalyticsQuery"

    # Detail
    VS_DETAIL = "VsHistoryDetailQuery"
    SALMON_DETAIL = "CoopHistoryDetailQuery"

    # Aliases
    TURF = "RegularBattleHistoriesQuery"
    COOP = "CoopHistoryQuery"
    ANARCHY_DETAIL = "VsHistoryDetailQuery"
    REGULAR_DETAIL = "VsHistoryDetailQuery"
    X_DETAIL = "VsHistoryDetailQuery"
    PRIVATE_DETAIL = "VsHistoryDetailQuery"
    LATEST_DETAIL = "VsHistoryDetailQuery"
    COOP_DETAIL = "CoopHistoryDetailQuery"

    @staticmethod
    def get(query: str) -> str:
        """Gets the query from the query map.

        Args:
            query (str): The query to get.

        Returns:
            str: The query.
        """
        return getattr(QueryMap, query.upper())


class SplatNet3_Scraper:
    """This class implements all of the classes and functions defined in the
    splatnet3_scraper.base module and can be seen as an example of how to put
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
    def from_config_file(config_file: str | None = None) -> "SplatNet3_Scraper":
        """Creates a new instance of the class using a configuration file. If
        no configuration file is provided, the default configuration file,
        .splatnet3_scraper, will be used.

        Args:
            config_file (str | None): The path to the configuration file. If
                None, the default configuration file will be used. Defaults to
                None.

        Returns:
            SplatNet3_Scraper: A new instance of the class.
        """
        config = Config(config_file)
        return SplatNet3_Scraper(config)

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
    def from_session_token(session_token: str) -> "SplatNet3_Scraper":
        """Creates a new instance of the class using a session token.

        Args:
            session_token (str): The session token.

        Returns:
            SplatNet3_Scraper: A new instance of the class.
        """
        token_manager = TokenManager.from_session_token(session_token)
        token_manager.generate_all_tokens()
        config = Config(token_manager=token_manager)
        return SplatNet3_Scraper(config)

    @staticmethod
    def from_env() -> "SplatNet3_Scraper":
        """Creates a new instance of the class using the environment
        variables.

        Returns:
            SplatNet3_Scraper: A new instance of the class.
        """
        config = Config.from_env()
        return SplatNet3_Scraper(config)

    @staticmethod
    def from_s3s_config(path: str) -> "SplatNet3_Scraper":
        """Creates a new instance of the class using the s3s config file.

        Returns:
            SplatNet3_Scraper: A new instance of the class.
        """
        config = Config.from_s3s_config(path)
        return SplatNet3_Scraper(config)

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

    def __get_query(self, query_name: str) -> dict:
        """Internal method to get the data from a query. If the query fails, it
        will try to generate all of the tokens and only once more. Not
        recommended to wrap this method in the retry decorator generator.

        Args:
            query_name (str): The name of the query to use.

        Returns:
            dict: The data from the query.
        """
        response = self.__query(query_name)
        if response.status_code != 200:
            self.config.token_manager.generate_all_tokens()
            response = self.__query(query_name)
        return response.json()["data"]

    def __get_detailed_query(self, game_id: str, versus: bool = True) -> dict:
        """Internal method to get the data from a detailed query. If the query
        fails, it will try to generate all of the tokens and only once more.
        Not recommended to wrap this method in the retry decorator generator.

        Args:
            game_id (str): The ID of the game to get the details from.
            versus (bool): Whether the game is a versus game or not. Defaults
                to True.

        Returns:
            dict: The data from the query.
        """
        name = QueryMap.VS_DETAIL if versus else QueryMap.SALMON_DETAIL
        variable_name = "vsResultId" if versus else "coopHistoryDetailId"
        response = self.__query(name, variables={variable_name: game_id})
        if response.status_code != 200:
            self.config.token_manager.generate_all_tokens()
            response = self.__query(name, variables={variable_name: game_id})
        return response.json()["data"]

    def get_mode_summary(
        self,
        mode: str,
        detailed: bool = False,
        detailed_limit: int | None = None,
    ) -> QueryResponse:
        """Gets the summary for a specific mode.

        Args:
            mode (str): The mode to get the summary for.
            detailed (bool): Whether to get the detailed summary or not.
                Defaults to False.
            detailed_limit (int | None): The maximum number of detailed
                matches to get. If None, all of the matches will be returned.

        Raises:
            ValueError: If the mode is invalid.

        Returns:
            QueryResponse: The summary for the mode.
        """
        try:
            query_name = QueryMap.get(mode)
        except AttributeError:
            raise ValueError(f"Invalid mode: {mode}")

        if not detailed:
            data = self.__get_query(query_name)
            return QueryResponse(data=data)
        summary, detailed_data = self.__vs_with_details(
            query_name, detailed_limit
        )
        return QueryResponse(data=summary, additional_data=detailed_data)

    def get_vs_detail(self, game_id: str) -> dict:
        """Gets the details of a versus game.

        Args:
            game_id (str): The ID of the game to get the details from.

        Returns:
            dict: The details of the game.
        """
        return self.__get_detailed_query(game_id)

    def get_salmon_detail(self, game_id: str) -> dict:
        """Gets the details of a salmon run game.

        Args:
            game_id (str): The ID of the game to get the details from.

        Returns:
            dict: The details of the game.
        """
        return self.__get_detailed_query(game_id, False)

    def __vs_with_details(
        self, query_name: str, limit: int | None = None
    ) -> tuple[dict, list[dict]]:
        """Internal method to get the data from a query and add the details to
        the data. If the query fails, it will try to generate all of the tokens
        and only once more. Not recommended to wrap this method in the retry
        decorator generator.

        Args:
            query_name (str): The name of the query to use.
            limit (int | None): The maximum number of detailed matches to get.
                If None, all of the matches will be returned. Defaults to None.

        Returns:
            tuple:
                dict: The data from the query.
                list[dict]: The details of the games, in order.
        """
        data = self.__get_query(query_name)
        if limit is None:
            limit = -1
        # Top level key depends on the game mode but there is only one top level
        # key so we can just get the first one.
        key = list(data.keys())[0]
        base = data[key]["historyGroups"]["nodes"]
        out: list[dict] = []
        idx = 0
        for group in base:
            for game in group["historyDetails"]["nodes"]:
                if idx == limit:
                    return data, out
                idx += 1
                game_id = game["id"]
                detailed_game = self.get_vs_detail(game_id)
                out.append(detailed_game)
        return data, out

    @retry(times=1, exceptions=ConnectionError)
    def query(self, query_name: str, variables: dict = {}) -> dict:
        """Queries Splatnet 3 and returns the data.

        Args:
            query_name (str): The name of the query to use.
            variables (dict): The variables to use in the query. Defaults to {}.

        Raises:
            SplatnetException: If the query was successful but returned at
                least one error.

        Returns:
            dict: The data from the query.
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
            raise SplatnetException(error_message)

        return QueryResponse(data=response.json()["data"])
