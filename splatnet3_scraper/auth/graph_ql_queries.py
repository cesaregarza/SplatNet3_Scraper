from __future__ import annotations

import json
from typing import Any

import requests

from splatnet3_scraper.constants import (
    DEFAULT_USER_AGENT,
    GRAPHQL_URL,
    SPLATNET_URL,
)
from splatnet3_scraper.utils import get_splatnet_hashes, get_splatnet_version


class GraphQLQueries:
    """The GraphQLQueries class that contains the GraphQL queries used by
    ``splatnet3_scraper``. The Nintendo Switch Online API only allows persistent
    queries, so making queries requires using the hashes for said queries. The
    great folks over at `imink` have a GitHub Actions workflow that checks for
    and updates the hashes for the queries every five minutes. The hashes are
    stored in a JSON file that is hosted on GitHub. This class automatically
    downloads the JSON file and stores the hashes in a dictionary. The hashes
    are then used to make queries to the Nintendo Switch Online API and can be
    accessed using their string names.
    """

    def __init__(self) -> None:
        """Initializes the GraphQLQueries class. Initializes a requests.Session
        and stores it in the session attribute. Also gets the hashes for the
        GraphQL queries and stores them in the hash_map attribute. The hashes
        are stored in a dictionary where the keys are the names of the queries
        and the values are the hashes.
        """
        self.session = requests.Session()

    def get_query(self, query_name: str) -> str:
        """Gets a GraphQL query hash given the name of the query.

        Uses the hash_map attribute to get the hash for the query, which is
        then returned. For more information on the valid queries, see the
        ``queries`` page of the documentation.

        Args:
            query_name (str): The name of the query.

        Returns:
            str: The GraphQL query hash.
        """
        return get_splatnet_hashes()[query_name]

    def query_header(
        self,
        bullet_token: str,
        language: str,
        user_agent: str | None = None,
        override: dict[str, str] = {},
    ) -> dict[str, str]:
        """Generates the headers that are used for the GraphQL queries made for
        the SplatNet 3 API.

        The headers are generated using the bullet token, language and user
        agent. Any headers that are passed in the override parameter will
        override the default headers. An example of the headers that are
        generated is shown below.

        >>> headers = {
        ...     "Authorization": f"Bearer {bullet_token}",
        ...     "Accept-Language": language,
        ...     "User-Agent": user_agent,
        ...     "X-Web-View-Ver": web_version,
        ...     "Content-Type": "application/json",
        ...     "Accept": "*/*",
        ...     "Origin": SPLATNET_URL,
        ...     "X-Requested-With": "com.nintendo.znca",
        ...     "Referer": (
        ...         f"{SPLATNET_URL}?"
        ...         f"lang={language}"
        ...         f"&na_country={language[-2:]}"
        ...         f"&na_lang={language}"
        ...     ),
        ...     "Accept-Encoding": "gzip, deflate",
        ... }

        Args:
            bullet_token (str): The bullet token.
            language (str): The language code to use, for example, "en-US".
            user_agent (str | None): The user agent to use. If None, the default
                user agent will be used. Defaults to None.
            override (dict[str, str]): Any headers that should override the
                default headers. Defaults to {}.

        Returns:
            dict[str, str]: The headers for the GraphQL queries.
        """

        if user_agent is None:
            user_agent = DEFAULT_USER_AGENT

        headers = {
            "Authorization": f"Bearer {bullet_token}",
            "Accept-Language": language,
            "User-Agent": user_agent,
            "X-Web-View-Ver": get_splatnet_version(),
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
        self, query_hash: str | bytes, variables: dict[str, Any] = {}
    ) -> str:
        """Generates the body for the GraphQL queries, as a string.

        The body is generated using the query hash and the variables that are
        passed in. The body is a JSON string that contains the query hash and
        the variables. An example of the body that is generated is shown
        below.

        >>> body = {
        ...     "extensions": {
        ...         "persistedQuery": {
        ...             "sha256Hash": query_hash,
        ...             "version": 1,
        ...         }
        ...     },
        ...     "variables": variables,
        ... }

        Args:
            query_hash (str | bytes): The hash of the query.
            variables (dict[str, Any]): The variables to pass to the query. If
                the query does not take any variables, this can be an empty
                dictionary. Defaults to {}.

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
        """Generates the body for the GraphQL queries, as a string.

        This method is a wrapper around the ``query_body_hash`` method. It gets
        the query hash using the ``get_query`` method and then calls the
        ``query_body_hash`` method to generate the body. For more information on
        the valid queries, see the `queries` page of the documentation.

        Args:
            query_name (str): The name of the query.
            variables (dict[str, str]): The variables to pass to the query. If
                the query does not take any variables, this can be an empty
                dictionary. Defaults to {}.

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
        variables: dict[str, Any] = {},
        override: dict[str, Any] = {},
    ) -> requests.Response:
        """Makes a GraphQL query using the persisted query hash. This method
        generates the headers and body for the query and then makes the
        request. For more information on the valid queries, see the `queries`
        page of the documentation.

        Args:
            query_hash (str | bytes): The hash of the query.
            bullet_token (str): The bullet token.
            gtoken (str): The gtoken.
            language (str): The language code to use.
            user_agent (str | None): The user agent to use. If None, the default
                user agent will be used. Defaults to None.
            variables (dict[str, Any]): The variables to pass to the query. If
                the query does not take any variables, this can be an empty
                dictionary. Defaults to an empty dictionary.
            override (dict[str, Any]): Any headers that should override the
                default headers. Defaults to an empty dictionary.

        Returns:
            requests.Response: The response from the GraphQL query.
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
        variables: dict[str, Any] = {},
        override: dict[str, Any] = {},
    ) -> requests.Response:
        """Makes a GraphQL query. This method is a wrapper around the
        ``query_hash`` method. It gets the query hash using the ``get_query``
        method and then calls the ``query_hash`` method to make the request. For
        more information on the valid queries, see the `queries` page of the
        documentation.

        Args:
            query_name (str): The name of the query.
            bullet_token (str): The bullet token.
            gtoken (str): The gtoken.
            language (str): The language code to use.
            user_agent (str | None): The user agent to use. If None, the default
                user agent will be used. Defaults to None.
            variables (dict[str, Any]): The variables to pass to the query. If
                the query does not take any variables, this can be an empty
                dictionary. Defaults to an empty dictionary.
            override (dict[str, Any]): Any headers that should override the
                default headers. Defaults to an empty dictionary.

        Returns:
            requests.Response: The response from the GraphQL query.
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
