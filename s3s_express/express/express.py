import requests

from s3s_express.base.graph_ql_queries import queries
from s3s_express.base.tokens import NSO, TokenManager
from s3s_express.constants import TOKENS
from s3s_express.express.config import Config


class QueryMap:
    ANARCHY = "BankaraBattleHistoriesQuery"
    REGULAR = "RegularBattleHistoriesQuery"
    X = "XBattleHistoriesQuery"
    PRIVATE = "PrivateBattleHistoriesQuery"
    LATEST = "LatestBattleHistoriesQuery"
    SALMON = "CoopHistoryQuery"

    # Aliases
    BATTLE = ANARCHY
    TURF = REGULAR


class S3S_Express:
    """This class implements all of the classes and functions defined in the
    s3s_express.base module and can be seen as an example of how to put them
    together. While the class has a method to create the session token, a full
    implementation with a CLI is outside the scope of this project.
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
    def from_config_file(config_file: str | None = None) -> "S3S_Express":
        """Creates a new instance of the class using a configuration file. If
        no configuration file is provided, the default configuration file,
        .s3s_express, will be used.

        Args:
            config_file (str | None): The path to the configuration file. If
                None, the default configuration file will be used. Defaults to
                None.

        Returns:
            S3S_Express: A new instance of the class.
        """
        config = Config(config_file)
        return S3S_Express(config)

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
    def from_session_token(session_token: str) -> "S3S_Express":
        """Creates a new instance of the class using a session token.

        Args:
            session_token (str): The session token.

        Returns:
            S3S_Express: A new instance of the class.
        """
        token_manager = TokenManager.from_session_token(session_token)
        token_manager.generate_all_tokens()
        config = Config(token_manager=token_manager)
        return S3S_Express(config)

    def __query(self, query_name: str) -> requests.Response:
        """Internal method to query Splatnet 3, it does all of the heavy lifting
        and is used by the other methods to get the data.

        Args:
            query_name (str): The name of the query to use.

        Returns:
            requests.Response: The response from the query.
        """
        return queries.query(
            query_name,
            self.config.get_token(TOKENS.BULLET_TOKEN),
            self.config.get_token(TOKENS.GTOKEN),
            self.config.get_data("language"),
            self.config.get("user_agent"),
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
        return self.__query(query_name).json()["data"]

    def get_anarchy(self) -> dict:
        """Gets the battle queries.

        Returns:
            dict: The battle queries.
        """
        return self.__get_query(QueryMap.ANARCHY)

    def get_regular(self) -> dict:
        """Gets the turf queries.

        Returns:
            dict: The turf queries.
        """
        return self.__get_query(QueryMap.REGULAR)

    def get_x(self) -> dict:
        """Gets the X queries.

        Returns:
            dict: The X queries.
        """
        return self.__get_query(QueryMap.X)

    def get_private(self) -> dict:
        """Gets the private queries.

        Returns:
            dict: The private queries.
        """
        return self.__get_query(QueryMap.PRIVATE)

    def get_latest(self) -> dict:
        """Gets the latest queries.

        Returns:
            dict: The latest queries.
        """
        return self.__get_query(QueryMap.LATEST)

    def get_salmon(self) -> dict:
        """Gets the salmon queries.

        Returns:
            dict: The salmon queries.
        """
        return self.__get_query(QueryMap.SALMON)
