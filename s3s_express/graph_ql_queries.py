from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

import requests

from s3s_express.constants import (
    DEFAULT_USER_AGENT,
    GRAPH_QL_REFERENCE_URL,
    GRAPHQL_URL,
    SPLATNET_URL,
)

if TYPE_CHECKING:
    # Prevent circular imports since this is only used for type hints.
    from s3s_express.tokens import TokenManager

from s3s_express.config import Config
from s3s_express.utils import get_splatnet_web_version


class GraphQLQueries:
    """Class that contains the GraphQL queries used by s3s_express.

    Attributes:
        hash_map (dict[str, str]): The hashes for the GraphQL queries.
    """

    def __init__(self) -> None:
        """Initializes the class."""
        self.hash_map = self.get_hashes()

    @staticmethod
    def get_hashes() -> dict[str, str]:
        """Gets the hashes for the GraphQL queries.

        Returns:
            dict[str, str]: The hashes for the GraphQL queries.
        """
        response = requests.get(GRAPH_QL_REFERENCE_URL)
        hash_map = response.json()["graphql"]["hash_map"]
        return hash_map

    def get_query(self, query_name: str) -> str:
        """Gets a GraphQL query.

        Args:
            query_name (str): The name of the query.

        Returns:
            str: The GraphQL query.
        """
        return self.hash_map[query_name]

    def query_header(
        self,
        token_manager: TokenManager,
        config: Config | str | None = None,
        override: dict[str, str] = {},
    ) -> dict[str, str]:
        """Gets the headers for the GraphQL queries.

        Args:
            token_manager (TokenManager): The token manager.
            config (Config, str): The config file or a string containing the
                desired user agent. If None, the default user agent will be
                used. Defaults to None.
            override (dict[str, str]): The headers to override. Defaults to an
                empty dictionary.

        Returns:
            dict[str, str]: The headers for the GraphQL queries.
        """
        if "language" in override:
            language = override["language"]
        else:
            language = token_manager.data["language"]

        if config is None:
            user_agent = DEFAULT_USER_AGENT
        elif isinstance(config, Config):
            user_agent = config.get("user_agent")
        else:
            user_agent = config

        headers = {
            "Authorization": f"Bearer {token_manager.get('bullet_token')}",
            "Accept-Language": language,
            "User-Agent": user_agent,
            "X-Web-View-Ver": get_splatnet_web_version(),
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": SPLATNET_URL,
            "X-Requested-With": "com.nintendo.znca",
            "Referer": (
                f"{SPLATNET_URL}?"
                f"lang={language}"
                f"&na_country={language[-2:]}"
                f"&na_lang={language}"
            ),
            "Accept-Encoding": "gzip, deflate",
        }
        headers.update(override)
        return headers

    def query_body(
        self, query_name: str, variables: dict[str, str] = {}
    ) -> str:
        """Gets the body for the GraphQL queries, as a string.

        Args:
            query_name (str): The name of the query.
            variables (dict[str, str]): The variables for the query.

        Returns:
            str: The body for the GraphQL queries, as a string.
        """
        out = {
            "extensions": {
                "persistedQuery": {
                    "sha256Hash": self.get_query(query_name),
                    "version": 1,
                }
            },
            "variables": variables,
        }
        return json.dumps(out)

    def query(
        self,
        query_name: str,
        token_manager: TokenManager,
        config: Config | None = None,
        variables: dict[str, str] = {},
        override: dict[str, str] = {},
    ) -> requests.Response:
        """Makes a GraphQL query.

        Args:
            query_name (str): The name of the query.
            token_manager (TokenManager): The token manager.
            config (Config): The config for the query. Defaults to None.
            variables (dict[str, str]): The variables for the query. Defaults to
                an empty dictionary.
            override (dict[str, str]): The headers to override. Defaults to an
                empty dictionary.

        Returns:
            requests.Response: The response from the query.
        """
        header = self.query_header(token_manager, config, override)
        body = self.query_body(query_name, variables)
        cookies = {
            "_gtoken": cast(str, token_manager.get("gtoken")),
        }
        response = requests.post(
            GRAPHQL_URL, headers=header, data=body, cookies=cookies
        )
        return response


queries = GraphQLQueries()
