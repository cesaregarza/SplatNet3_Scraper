import json
import logging

import requests

from splatnet3_scraper.auth import NSO, TokenManager
from splatnet3_scraper.auth.exceptions import SplatNetException
from splatnet3_scraper.auth.graph_ql_queries import queries
from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.query.config import Config
from splatnet3_scraper.query.responses import QueryResponse
from splatnet3_scraper.utils import retry


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
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized QueryHandler.")

    @staticmethod
    def from_config_file(
        config_path: str | None = None,
    ) -> "QueryHandler":
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

        Returns:
            QueryHandler: A new instance of the class using the configuration
                file provided, with all the options set in the configuration
                file.
        """
        config = Config(config_path)
        return QueryHandler(config)

    @staticmethod
    def generate_session_token_url(
        user_agent: str | None = None,
    ) -> tuple[str, bytes, bytes]:
        """Generates the URL to use to get the session token.

        This method is used to generate the URL to use to get the session token
        from the Nintendo Switch Online website. The user must then visit this
        URL in their browser and log in to their Nintendo account. Once they
        have logged in, they will be redirected to a page that contains the user
        profile to select. The user must then select their user profile and
        then copy the URL from the "select this account" button. The URI of the
        button will contain the session token code, which the user must then
        pass to the ``parse_npf_uri`` method to get the session token. This
        method is currently incomplete and will be updated in the future with
        its counterpart method to parse the URI and return a ``QueryHandler``
        object with a valid session token already set in the ``Config`` object
        and saved to the default configuration path in the user's current
        working directory.

        Args:
            user_agent (str | None): The user agent to use when making the
                initial requests to the Nintendo Switch Online service. If None,
                the default user agent will be used. It is not recommended to
                change this unless you know what you are doing. Defaults to
                None.

        Returns:
            str: The URL to use to get the session token.
            bytes: The state ID.
            bytes: The challenge solution.
        """
        nso = NSO.new_instance()
        url = nso.generate_login_url(user_agent)
        return url, nso.state, nso.verifier

    @staticmethod
    def from_session_token(session_token: str) -> "QueryHandler":
        """Creates a new instance of the class using a session token.

        Given a session token, this method will create a new instance of the
        class with a valid session token already set in the ``Config`` object.
        This method is useful if the user already has a session token and does
        not want to generate an accompanying ``GTOKEN`` and ``BULLET_TOKEN``.

        Args:
            session_token (str): The session token to use. This token must be
                valid and not expired or revoked. If the token is invalid, the
                user will not be able to make any queries to the SplatNet 3 API.

        Returns:
            QueryHandler: A new instance of the class with a valid session
                token already set in the ``Config`` object. The ``GTOKEN`` and
                ``BULLET_TOKEN`` will also have been generated and set in the
                ``Config`` object.
        """
        token_manager = TokenManager.from_session_token(session_token)
        token_manager.generate_all_tokens()
        config = Config(token_manager=token_manager)
        return QueryHandler(config)

    @staticmethod
    def from_tokens(
        session_token: str,
        gtoken: str | None = None,
        bullet_token: str | None = None,
    ) -> "QueryHandler":
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

        Returns:
            QueryHandler: A new instance of the class with all the tokens
                already set in the ``Config`` object.
        """
        token_manager = TokenManager.from_tokens(
            session_token, gtoken, bullet_token
        )
        config = Config(token_manager=token_manager)
        return QueryHandler(config)

    @staticmethod
    def from_env() -> "QueryHandler":
        """Creates a new instance of the class using the environment
        variables.

        This method will create a new instance of the class using the
        environment variables. This method is useful if the user wants to start
        up the class in a CI/CD pipeline, a Docker container, or any other
        environment where the user does not want to store the session token in
        a file. The environment variables that this method will use are
        prepended by ``SN3S_`` and are all uppercase. The three environment
        variables supported are:

        - ``SN3S_SESSION_TOKEN``: The session token to use. This token must be
            valid and not expired or revoked.
        - ``SN3S_GTOKEN``: The GTOKEN to use.
        - ``SN3S_BULLET_TOKEN``: The BULLET_TOKEN to use.

        Returns:
            QueryHandler: A new instance of the class with a valid session
                token already set in the ``Config`` object. The ``Config``
                object is also flagged as using environment variables, so the
                user does not need to worry about accidentally saving the
                session token to disk.
        """
        config = Config.from_env()
        return QueryHandler(config)

    @staticmethod
    def from_s3s_config(path: str) -> "QueryHandler":
        """Creates a new instance of the class using the ``s3s`` config file.

        This method will create a new instance of the class by reading the
        ``s3s`` config file. The ``s3s`` config file is a file that is used by
        ``s3s`` to store the user's data. This method is useful if the user
        already has a ``s3s`` config file. The ``s3s`` config file is a JSON
        file that contains the user's session token, G token, bullet token, and
        other options and data.

        Args:
            path (str): The path to the s3s config file. This file must be a
                valid JSON file.

        Returns:
            QueryHandler: A new instance of the class from the ``s3s`` config
                file provided.
        """
        config = Config.from_s3s_config(path)
        return QueryHandler(config)

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
        response = self.__query_hash(query_hash, variables)
        if response.status_code != 200:
            self.logger.info("Query failed, regenerating tokens and retrying.")
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
        response = self.__query(query_name, variables)
        if response.status_code != 200:
            self.logger.info("Query failed, regenerating tokens and retrying.")
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

    def export_tokens(self) -> list[tuple[str, str]]:
        """Exports the tokens to a list of tuples.

        This method will export the tokens to a list of tuples. This method is
        useful if the user wants to export the tokens to a file or to a database
        or some other data store. The tokens are returned as a list of tuples
        with the first element being the token name and the second element being
        the token value. The list of tokens returned is as follows:

        - ``session_token``
        - ``gtoken``
        - ``bullet_token``

        Returns:
            list[tuple[str, str]]: The list of tokens as a list of tuples.
        """
        self.logger.debug("Exporting tokens.")
        return self.config.token_manager.export_tokens()
