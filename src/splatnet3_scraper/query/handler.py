from __future__ import annotations

import json
import logging
from typing import cast

import requests

from splatnet3_scraper.auth.exceptions import SplatNetException
from splatnet3_scraper.auth.graph_ql_queries import queries
from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.query.config import Config
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

    def __init__(self, config: Config) -> None:
        """Initializes the class, it is not meant to be instantiated directly,
        but rather through one of the available factory methods. Still, it can
        be instantiated directly if the user wants to use a custom Config class.

        Args:
            config (Config): The Config object to use. This object contains all
                the configuration options that the user can set, and the
                QueryHandler class will use these options as they are needed
                throughout the operation of the class. It is recommended that
                the user uses the factory methods to create a new instance of
                the class instead of instantiating it directly, as the factory
                methods will automatically create a Config object for the user
                based on the instantiation method they prefer and pass it to the
                constructor.
        """
        self.config = config
        logging.info("Initialized QueryHandler")

    @classmethod
    def from_config_file(
        cls,
        config_path: str | None = None,
        *,
        prefix: str = "",
    ) -> QueryHandler:
        """Creates a new instance of the class using a configuration file.

        If the user does not provide a configuration file path, the default path
        will be used, which is ``.splatnet3_scraper`` in the user's current
        working directory. The configuration file this method accepts is one
        that aligns with the standard configuration file format used by the
        standard library ``configparser`` module. The configuration file must
        have a ``[Tokens]`` section, which only requires the ``session_token``
        option to be set. The ``session_token`` option must be set to the user's
        session token. For a full list of all options that can be set in the
        config file, see the documentation for the ``Config`` class.

        Args:
            config_path (str | None): The path to the configuration file. If
                None, the default configuration file path of
                ``.splatnet3_scraper`` in the user's current working directory
                will be used. Defaults to None.
            prefix (str): The prefix to use for environment variables. This is
                useful if the user prefers to use both environment variables and
                configuration files. Defaults to "SN3S".

        Returns:
            QueryHandler: A new instance of the class using the configuration
                file provided, with all the options set in the configuration
                file.
        """
        path = config_path or Config.DEFAULT_CONFIG_PATH
        config = Config.from_file(path, prefix=prefix)
        return cls(config)

    @classmethod
    def from_tokens(
        cls,
        session_token: str,
        gtoken: str | None = None,
        bullet_token: str | None = None,
        *,
        prefix: str = "",
    ) -> QueryHandler:
        """Creates a new instance of the class using the tokens provided.

        Given a session token, a ``GTOKEN``, and a ``BULLET_TOKEN``, this
        method will create a new instance of the class with all the tokens
        already set in the ``Config`` object. This method is useful if the user
        already has all the tokens and wants to avoid having to generate them
        again if possible. If the user does not have all the tokens, they can
        pass in ``None`` for the tokens they do not have and the method will
        generate the tokens that are missing.

        Args:
            session_token (str): The session token to use. This token must be
                valid and not expired or revoked. If the token is invalid, the
                user will not be able to make any queries to the SplatNet 3 API.
            gtoken (str | None): The ``GTOKEN`` to use. If None, the method
                will generate a new ``GTOKEN``. Defaults to None.
            bullet_token (str | None): The ``BULLET_TOKEN`` to use. If None,
                the method will generate a new ``BULLET_TOKEN``. Defaults to
                None.
            prefix (str): The prefix to use for the configuration options. This
                is useful if the user wants to use multiple instances of the
                class with different tokens. Defaults to "SN3S".

        Returns:
            QueryHandler: A new instance of the class with all the tokens
                already set in the ``Config`` object.
        """
        config = Config.from_tokens(
            session_token=session_token,
            gtoken=gtoken,
            bullet_token=bullet_token,
            prefix=prefix,
        )
        return cls(config)

    @classmethod
    def from_session_token(
        cls,
        session_token: str,
        *,
        prefix: str = "",
    ) -> QueryHandler:
        """Creates a new instance of the class using a session token.

        Given a session token, this method will create a new instance of the
        class with a valid session token already set in the ``Config`` object.
        This method is useful if the user already has a session token and does
        not want to generate an accompanying ``GTOKEN`` and ``BULLET_TOKEN``.

        Args:
            session_token (str): The session token to use. This token must be
                valid and not expired or revoked. If the token is invalid, the
                user will not be able to make any queries to the SplatNet 3 API.
            prefix (str): The prefix to use for the configuration options. This
                is useful if the user wants to use multiple instances of the
                class with different tokens. Defaults to "SN3S".

        Returns:
            QueryHandler: A new instance of the class with a valid session
                token already set in the ``Config`` object. The ``GTOKEN`` and
                ``BULLET_TOKEN`` will also have been generated and set in the
                ``Config`` object.
        """
        config = Config.from_tokens(
            session_token=session_token,
            prefix=prefix,
        )
        config.regenerate_tokens()
        return cls(config)

    @classmethod
    def new_instance(
        cls,
        *,
        prefix: str = "",
    ) -> QueryHandler:
        """Creates a new instance of the class.

        This method will create a new instance of the class with no tokens set
        in the ``Config`` object. This method is useful if the user wants to
        generate all the tokens themselves. The user can then use the
        ``add_token`` method to add the tokens to the ``Config`` object.

        Args:
            prefix (str): The prefix to use for the configuration options. This
                is useful if the user wants to use multiple instances of the
                class with different tokens. Defaults to "SN3S".

        Returns:
            QueryHandler: A new instance of the class with no tokens set in the
                ``Config`` object.
        """
        config = Config.from_empty_handler(prefix=prefix)
        return cls(config)

    @classmethod
    def from_s3s_config(
        cls,
        path: str,
        *,
        prefix: str = "",
    ) -> QueryHandler:
        """Creates a new instance of the class from an s3s configuration file.

        This method will create a new instance of the class using an s3s
        configuration file. This method is useful if the user is a previous user
        of ``s3s`` and wants to migrate to ``splatnet3_scraper``.

        Args:
            path (str): The path to the configuration file.
            prefix (str): The prefix to use for environment variables. This is
                useful if the user prefers to use both environment variables and
                configuration files. Defaults to "SN3S".

        Returns:
            QueryHandler: A new instance of the class using the configuration
                file provided, with all the options set in the configuration
                file.
        """
        config = Config.from_s3s_config(path, prefix=prefix)
        return cls(config)

    def raw_query(
        self,
        query_name: str,
        language: str | None = None,
        variables: dict = {},
    ) -> requests.Response:
        """Makes a raw query to the SplatNet 3 API.

        This method is used to make a raw query to the SplatNet 3 API. It is not
        recommended that the user use this method directly, but rather use the
        ``query`` method instead, as it will handle all the token management
        automatically. This method is rarely useful, but it is provided for
        completeness... and because I don't like hidden methods all that much.

        Args:
            query_name (str): The name of the query to use.
            language (str | None): The language to use for the query. If None,
                the language loaded into the ``Config`` object will be used.
                Defaults to None.
            variables (dict): The variables to use in the query. Defaults to {}.

        Returns:
            requests.Response: The response from the query.
        """
        return queries.query(
            query_name,
            cast(str, self.config.get_value(TOKENS.BULLET_TOKEN)),
            cast(str, self.config.get_value(TOKENS.GTOKEN)),
            language or cast(str, self.config.get_value("language")),
            self.config.get_value("user_agent"),
            variables=variables,
        )

    def raw_query_hash(
        self,
        query_hash: str,
        language: str | None = None,
        variables: dict = {},
    ) -> requests.Response:
        """Makes a raw query to the SplatNet 3 API using the query hash.

        This method is used to make a raw query to the SplatNet 3 API. It is not
        recommended that the user use this method directly, but rather use the
        ``query`` method instead, as it will handle all the token management
        automatically. If you MUST use a raw query, it is recommended that you
        use the ``raw_query`` method instead. This method is even more rarely
        useful than the ``raw_query`` method, but it is provided for
        completeness.

        Args:
            query_hash (str): The GraphQL query hash to use.
            language (str | None): The language to use for the query. If None,
                the language loaded into the ``Config`` object will be used.
                Defaults to None.
            variables (dict): The variables to use in the query. Defaults to {}.

        Returns:
            requests.Response: The response from the query.
        """
        return queries.query_hash(
            query_hash,
            cast(str, self.config.get_value(TOKENS.BULLET_TOKEN)),
            cast(str, self.config.get_value(TOKENS.GTOKEN)),
            language or cast(str, self.config.get_value("language")),
            self.config.get_value("user_agent"),
            variables=variables,
        )

    @retry(times=1, exceptions=ConnectionError)
    def query_hash(
        self,
        query_hash: str,
        language: str | None = None,
        variables: dict = {},
    ) -> QueryResponse:
        """Given a query hash, it will query SplatNet 3 and return the response.

        A convenience function that will use a GraphQL query hash rather than a
        query name to query SplatNet 3. This method will automatically retry
        once if the query fails and will regenerate the tokens if the query
        fails for whatever reason. Some queries require variables to be passed
        in, and this method will allow the user to pass in those variables. It
        is not recommended to use this method unless the user knows what they
        are doing, as the query hashes are not stable and can and do change
        often and without warning. The user should use the ``query`` method
        instead as it will compensate for any changes to the query hashes.

        Args:
            query_hash (str): The query hash to use. This hash must be valid,
                and must be a string representation rather than a byte
                representation.
            language (str | None): The language to use for the query. If None,
                the language loaded into the ``Config`` object will be used.
                Defaults to None.
            variables (dict): The variables to use in the query. Some queries do
                not require variables and so this argument can be omitted. If
                the query does require variables and this argument is omitted,
                then the query will fail and a ``SplatNetException`` will be
                raised with the error message from SplatNet 3. Defaults to {}.

        Raises:
            SplatNetException: If the query is successful but returns a JSON
                object with an ``errors`` key, then this exception will be
                raised with the error message from SplatNet 3. This generally
                means that the query was successfully generated and the current
                tokens are still valid, but the query itself failed for some
                reason. This can happen if the user did not provide the correct
                required variables for the query, or if the variables provided
                were somehow invalid.

        Returns:
            QueryResponse: The response from the query. This object will contain
                the data from the query, and will also contain the query hash
                that was used to generate the query. This is useful for
                debugging purposes.
        """
        response = self.raw_query_hash(query_hash, language, variables)
        if response.status_code != 200:
            logger.info("Query failed, regenerating tokens and retrying")
            self.config.regenerate_tokens()
            response = self.raw_query_hash(query_hash, language, variables)

        if "errors" in response.json():
            errors = response.json()["errors"]
            error_message = (
                "Query was successful but returned at least one error."
            )
            error_message += " Errors: " + json.dumps(errors, indent=4)
            raise SplatNetException(error_message)
        return QueryResponse(data=response.json()["data"])

    @retry(times=1, exceptions=ConnectionError)
    def query(
        self, query_name: str, language: str | None = None, variables: dict = {}
    ) -> QueryResponse:
        """Queries Splatnet 3 and returns the data.

        This method will query SplatNet 3 and return the data from the query.
        This method will automatically retry once if the query fails and will
        regenerate the tokens if the query fails for whatever reason. Some
        queries require variables to be passed in, and this method will allow
        the user to pass in those variables. This method obtains the query hash
        from the ``auth`` module and automatically uses the appropriate query
        hash for the query name provided. As such, it is recommended to use this
        method rather than the ``query_hash`` method unless the user knows what
        they are doing.

        Args:
            query_name (str): The name of the query to use. This name must be
                valid, and is not case sensitive. For more information on the
                list of valid queries, see the documentation on the queries that
                are available.
            language (str | None): The language to use for the query. If None,
                the language loaded into the ``Config`` object will be used.
                Defaults to None.
            variables (dict): The variables to use in the query. Some queries do
                not require variables and so this argument can be omitted. If
                the query does require variables and this argument is omitted,
                then the query will fail and a ``SplatNetException`` will be
                raised with the error message from SplatNet 3. Defaults to {}.

        Raises:
            SplatNetException: If the query is successful but returns a JSON
                object with an ``errors`` key, then this exception will be
                raised with the error message from SplatNet 3. This generally
                means that the query was successfully generated and the current
                tokens are still valid, but the query itself failed for some
                reason. This can happen if the user did not provide the correct
                required variables for the query, or if the variables provided
                were somehow invalid.

        Returns:
            QueryResponse: The response from the query. This object will contain
                the data from the query, and will also contain the query hash
                that was used to generate the query. This is useful for
                debugging purposes.
        """
        response = self.raw_query(query_name, language, variables)
        if response.status_code != 200:
            logger.info("Query failed, regenerating tokens and retrying.")
            self.config.regenerate_tokens()
            response = self.raw_query(query_name, language, variables)

        if "errors" in response.json():
            errors = response.json()["errors"]
            error_message = (
                "Query was successful but returned at least one error."
            )

            error_message += " Errors: " + json.dumps(errors, indent=4)
            raise SplatNetException(error_message)

        return QueryResponse(data=response.json()["data"])
