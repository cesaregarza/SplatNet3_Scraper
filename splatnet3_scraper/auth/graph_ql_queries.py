from __future__ import annotations

import json

import requests

from splatnet3_scraper.constants import (
    DEFAULT_USER_AGENT,
    GRAPH_QL_REFERENCE_URL,
    GRAPHQL_URL,
    SPLATNET_URL,
)
from splatnet3_scraper.utils import get_splatnet_web_version


class GraphQLQueries:
    """Class that contains the GraphQL queries used by splatnet3_scraper.

    Attributes:
        hash_map (dict[str, str]): The hashes for the GraphQL queries.
    """

    def __init__(self) -> None:
        """Initializes the class."""
        self.session = requests.Session()
        self.hash_map = self.get_hashes()

    def get_hashes(self) -> dict[str, str]:
        """Gets the hashes for the GraphQL queries.

        Returns:
            dict[str, str]: The hashes for the GraphQL queries.
        """
        response = self.session.get(GRAPH_QL_REFERENCE_URL)
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
        bullet_token: str,
        language: str,
        user_agent: str | None = None,
        override: dict[str, str] = {},
    ) -> dict[str, str]:
        """Gets the headers for the GraphQL queries.

        Args:
            bullet_token (str): The bullet token.
            language (str): The language code to use.
            user_agent (str | None): The user agent to use. If None, the default
                user agent will be used. Defaults to None.
            override (dict[str, str]): The headers to override. Defaults to an
                empty dictionary.

        Returns:
            dict[str, str]: The headers for the GraphQL queries.
        """

        if user_agent is None:
            user_agent = DEFAULT_USER_AGENT

        headers = {
            "Authorization": f"Bearer {bullet_token}",
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

    def query_body_hash(
        self, query_hash: str | bytes, variables: dict[str, str] = {}
    ) -> str:
        """Gets the body for the GraphQL queries, as a string.

        Args:
            query_hash (str | bytes): The hash of the query.
            variables (dict[str, str]): The variables for the query.

        Returns:
            str: The body for the GraphQL queries, as a string.
        """
        out = {
            "extensions": {
                "persistedQuery": {
                    "sha256Hash": query_hash,
                    "version": 1,
                }
            },
            "variables": variables,
        }
        return json.dumps(out)

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
        query = self.get_query(query_name)
        return self.query_body_hash(query, variables)

    def query_hash(
        self,
        query_hash: str | bytes,
        bullet_token: str,
        gtoken: str,
        language: str,
        user_agent: str | None = None,
        variables: dict[str, str] = {},
        override: dict[str, str] = {},
    ) -> requests.Response:
        """Makes a GraphQL query using the persisted query hash.

        Args:
            query_hash (str | bytes): The hash of the query.
            bullet_token (str): The bullet token.
            gtoken (str): The gtoken.
            language (str): The language code to use.
            user_agent (str | None): The user agent to use. If None, the default
                user agent will be used. Defaults to None.
            variables (dict[str, str]): The variables for the query. Defaults to
                an empty dictionary.
            override (dict[str, str]): The headers to override. Defaults to an
                empty dictionary.

        Returns:
            requests.Response: The response from the query.
        """
        header = self.query_header(bullet_token, language, user_agent, override)
        body = self.query_body_hash(query_hash, variables)
        cookies = {
            "_gtoken": gtoken,
        }
        return self.session.post(
            GRAPHQL_URL, headers=header, data=body, cookies=cookies
        )

    def query(
        self,
        query_name: str,
        bullet_token: str,
        gtoken: str,
        language: str,
        user_agent: str | None = None,
        variables: dict[str, str] = {},
        override: dict[str, str] = {},
    ) -> requests.Response:
        """Makes a GraphQL query using the query name to get the hash.

        Args:
            query_name (str): The name of the query.
            bullet_token (str): The bullet token.
            gtoken (str): The gtoken.
            language (str): The language code to use.
            user_agent (str | None): The user agent to use. If None, the default
                user agent will be used. Defaults to None.
            variables (dict[str, str]): The variables for the query. Defaults to
                an empty dictionary.
            override (dict[str, str]): The headers to override. Defaults to an
                empty dictionary.

        Returns:
            requests.Response: The response from the query.
        """
        query = self.get_query(query_name)
        return self.query_hash(
            query,
            bullet_token,
            gtoken,
            language,
            user_agent,
            variables,
            override,
        )


queries = GraphQLQueries()
