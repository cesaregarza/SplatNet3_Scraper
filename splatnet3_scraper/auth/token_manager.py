import configparser
import json
import logging
import os
import re
import time
from typing import Any, Literal, cast, overload

import requests

from splatnet3_scraper import __version__
from splatnet3_scraper.auth.environment_manager import (
    EnvironmentVariablesManager,
)
from splatnet3_scraper.auth.exceptions import (
    NintendoException,
    SplatNetException,
)
from splatnet3_scraper.auth.graph_ql_queries import queries
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.constants import (
    ENV_VAR_NAMES,
    GRAPH_QL_REFERENCE_URL,
    TOKEN_EXPIRATIONS,
    TOKENS,
)
from splatnet3_scraper.utils import retry

text_config_re = re.compile(r"\s*=*\s*")


class Token:
    """Class that represents a token. This class is meant to store the token
    itself, the type of token it is, and the time it was created. It can be used
    to check if the token is expired or display the time left before it expires.
    It also provides convenience methods for getting all sorts of metadata about
    the token.
    """

    def __init__(self, token: str, token_type: str, timestamp: float) -> None:
        """Initializes a ``Token`` object. The expiration time is calculated
        based on the token type, with a default of ``1e10`` seconds (about 316
        days, this should be basically forever for all intents and purposes; if
        you have a python session running for that long, you have bigger
        problems than a token expiring).

        Args:
            token (str): The value of the token, this is the actual token.
            token_type (str): The type of token, this is used to identify which
                type of token it represents, making it easier for the manager
                to handle the tokens when searching for a specific one. It also
                determines the expiration time of the token.
            timestamp (float): The time the token was created, in seconds since
                the epoch. This is used to determine if the token is expired.
        """
        self.token = token
        self.token_type = token_type
        self.timestamp = timestamp
        self.expiration = TOKEN_EXPIRATIONS.get(token_type, 1e10) + timestamp

    @property
    def is_valid(self) -> bool:
        """A very rudimentary check to see if the token is valid. This is not
        a guarantee that the token is valid, but it is a good indicator that
        it is for most cases. It checks if the token is not None and if it is
        not an empty string. This usually means that the token is valid, but
        it is not a guarantee. This is also here in case a future version of
        the API requires a different check to determine if a token is valid.

        Returns:
            bool: True if the token is valid (not None and not an empty string)
                False otherwise.
        """
        return (self.token is not None) and (self.token != "")

    @property
    def is_expired(self) -> bool:
        """Checks if the token is expired. This is done by comparing the
        current time to the expiration time of the token. If the current time
        is greater than the expiration time, the token is expired. This is not
        a guarantee that the token is expired, but it is a good indicator that
        it is for most cases.

        Returns:
            bool: True if the token is expired, False otherwise.
        """
        return self.time_left <= 0

    @property
    def time_left(self) -> float:
        """Returns the time left before the token expires. If the token is
        expired, a negative number will be returned. This is not a guarantee
        that the token is expired, but it is a good indicator that it is for
        most cases.

        Returns:
            float: The time left before the token expires.
        """
        return self.expiration - time.time()

    @property
    def time_left_str(self) -> str:
        """A string representation of the time left before the token expires.
        If the token is expired, "Expired" will be returned. This is not a
        guarantee that the token is expired, but it is a good indicator that
        it is for most cases. If the time left is greater than 100,000 hours,
        "basically forever" will be returned. If you have a python session
        running for that long, you have bigger problems than a token expiring.

        Returns:
            str: A string representation of the time left before the token
                expires.
        """
        time_left = self.time_left
        if time_left <= 0:
            return "Expired"
        mins, secs = divmod(time_left, 60)
        hours, mins = divmod(mins, 60)

        out = ""
        if hours > 1e5:
            return "basically forever"
        if hours > 0:
            out += f"{hours:.0f}h "
        if mins > 0:
            out += f"{mins:.0f}m "
        if secs > 0:
            out += f"{secs:.1f}s"
        return out.strip()

    def __repr__(self) -> str:
        out = "Token("
        spaces = " " * len(out)
        out += (
            f"token={self.token[:5]}...,\n"
            + spaces
            + f"type={self.token_type},\n"
            + spaces
            + "expires in "
            + self.time_left_str
            + "\n)"
        )
        return out


class TokenManager:
    """Class that manages tokens. This class can be used to add tokens, generate
    tokens from the ``NSO`` class, check if tokens are expired, load tokens from
    a configuration file or environment variables, save tokens to disk, and
    display the time left before tokens expire among other things.
    """

    def __init__(
        self,
        nso: NSO | None = None,
        *args,
        env_manager: EnvironmentVariablesManager | None = None,
    ) -> None:
        """Initializes a TokenManager object. This will create a new instance
        of the NSO class if one is not provided.

        Args:
            nso (NSO | None, optional): An instance of the NSO class. If one is
                not provided, a new instance will be created. Defaults to None.
            *args: Additional arguments to pass to the NSO class, currently not
                used.
            env_manager (EnvironmentVariablesManager): An instance of the
                EnvironmentVariablesManager class or a subclass of it. If not
                provided, a new instance will be created.
        """
        nso = nso if nso is not None else NSO.new_instance()
        self.nso = nso
        self._tokens: dict[str, Token] = {}
        self._data: dict[str, str] = {}
        self.env_manager = (
            env_manager
            if env_manager is not None
            else EnvironmentVariablesManager()
        )
        self.logger = logging.getLogger(__name__)

    def flag_origin(self, origin: str, data: str | None = None) -> None:
        """Flags the origin of the token manager. This is used to identify where
        the token manager was loaded from, if anywhere. This is used to help
        keep track of whether the user wants to save the tokens to disk or not,
        but can potentially be used for other things in the future. This is
        called automatically when the token manager is loaded from a config
        file or environment variables. Subsequent calls to this method will
        overwrite the previous origin.

        Args:
            origin (str): The origin of the token manager.
            data (str | None): Additional data about the origin. For example,
                if the token manager was loaded from a config file, this would
                be the path to the config file. On the other hand, if the token
                manager was loaded from environment variables, this would be
                None.
        """
        self._origin = {"origin": origin, "data": data}

    @property
    def origin(self) -> dict[str, str | None]:
        """Gets the origin of the token manager.

        This method is a thin wrapper around the ``_origin`` attribute. If the
        attribute does not exist, this method will return an empty dictionary
        but will not create the attribute. The attribute will only be created
        when the ``flag_origin`` method is called.

        Returns:
            dict[str, str | None]: The origin of the token manager. This will
                be a dictionary with two keys: ``origin`` and ``data``. The
                ``origin`` key will contain a string that describes where the
                token manager was loaded from. The ``data`` key will contain
                additional data about the origin. For example, if the token
                manager was loaded from a config file, this would be the path
                to the config file. On the other hand, if the token manager was
                loaded from environment variables, this would be None.
        """
        return getattr(self, "_origin", {})

    def add_token(
        self,
        token: str | Token,
        token_type: str | None = None,
        timestamp: float | None = None,
    ) -> None:
        """Adds a token to the manager. If the token provided is a ``string``,
        the token type must be provided as well. The manager will then create a
        new Token object and add it to its internal dictionary. If the token
        provided is a ``Token`` object, the object will be added to the manager
        as is.

        If the token type is ``session_token``, the token will

        Args:
            token (str | Token): The token to add to the manager. If a string,
                the token type must be provided as well. If a ``Token`` object,
                the token type will be ignored. This field might also be known
                as the "access token" or "auth token" among other names.
            token_type (str | None): The type of token. If token is an instance
                of ``Token``, this will be ignored. If token is a string, this
                must be provided. Currently the only supported token types that
                are recognized by the manager are "session_token", "gtoken", and
                "bullet_token". Defaults to None, which will cause an error to
                be raised if ``token`` is a string.
            timestamp (float | None): The time the token was created. If not
                provided, the current time will be used.

        Raises:
            ValueError: If the ``token`` provided is a string and ``token_type``
                is not provided.
        """
        self.logger.debug(f"Adding token of type {token_type} to manager.")
        if timestamp is None:
            timestamp = time.time()
        if isinstance(token, str) and token_type is None:
            raise ValueError(
                "arg token_type must be provided if token is a str."
            )
        elif isinstance(token, str) and token_type is not None:
            token_object = Token(token, token_type, timestamp)
        elif isinstance(token, Token):
            token_object = token

        self._tokens[token_object.token_type] = token_object
        if token_object.token_type == TOKENS.GTOKEN:
            self.nso._gtoken = token_object.token
        elif token_object.token_type == TOKENS.SESSION_TOKEN:
            self.nso._session_token = token_object.token

        return

    @overload
    def get(self, token_type: str, full_token: Literal[False] = ...) -> str:
        ...

    @overload
    def get(self, token_type: str, full_token: Literal[True]) -> Token:
        ...

    @overload
    def get(self, token_type: str, full_token: bool) -> str | Token:
        ...

    def get(self, token_type: str, full_token: bool = False) -> str | Token:
        """Gets a token from the manager given a token type.

        If ``full_token`` is True, the full ``Token`` object will be returned.
        Otherwise, just the value of the token will be returned. If the token
        type is not found, a ValueError will be raised.

        Args:
            token_type (str): The type of the token to get, as defined in the
                ``Token.token_type`` field.
            full_token (bool): Whether to return the full ``Token`` object or
                just the value of the token. Defaults to False.

        Raises:
            ValueError: If the given token type is not found in the manager.

        Returns:
            str | Token: The token, either as a string or a ``Token`` object as
                defined by the ``full_token`` argument.
        """
        token_obj = self._tokens.get(token_type, None)
        if token_obj is None:
            raise ValueError(f"Token of type {token_type} not found.")
        if full_token:
            return token_obj
        return token_obj.token

    @property
    def data(self) -> dict[str, Any]:
        """Returns the full data stored in the manager as a dictionary. This
        data is not the same as the tokens stored in the manager, but rather
        additional data that can be used in other places. Examples of keys that
        might be stored in this dictionary are the user's ``country``, and
        ``language`` as defined by the Nintendo Account.

        Returns:
            dict[str, Any]: The data stored in the manager as a dictionary.
        """
        return self._data

    def add_session_token(self, token: str) -> None:
        """Adds a session token to the manager. This is a convenience method
        that will also set the session token in the NSO class. This
        functionality is already present in the ``add_token`` method, so this
        method might be removed in the future.

        Args:
            token (str): The session token to add to the manager. This field
                might also be known as the "access token" or "auth token" among
                other names. This token is used to authenticate with Nintendo
                services, and is required to query the SplatNet 3 API.
        """
        self.add_token(token, TOKENS.SESSION_TOKEN)
        self.nso._session_token = token

    def generate_gtoken(self) -> None:
        """Generates a new gtoken from the internal NSO class and adds it to the
        manager. This is a convenience method that will also set the gtoken in
        the NSO class. This function requires a session token to already be
        set, and will raise a ValueError if it is not.

        Raises:
            ValueError: If the session token has not been set.
            NintendoException: In the unlikely event that the gtoken has made it
                through the NSO class but the user info was not set, this error
                provides a safety net to identify that there was a problem with
                the gtoken generation. Should not be raised in normal use.
        """
        if TOKENS.SESSION_TOKEN not in self._tokens:
            raise ValueError(
                "Session token must be set before generating a gtoken."
            )
        gtoken = self.nso.get_gtoken(self.nso.session_token)
        self.add_token(gtoken, TOKENS.GTOKEN)
        try:
            user_info = cast(dict[str, str], self.nso._user_info)
            country = user_info["country"]
            language = user_info["language"]
            self._data["country"] = country
            self._data["language"] = language
        except (KeyError, TypeError):
            raise NintendoException(
                "Unable to get user info. Gtoken may be invalid."
            )

    @retry(times=1, exceptions=SplatNetException)
    def generate_bullet_token(self) -> None:
        """Generates a new bullet token from the internal NSO class and adds it
        to the manager. This is a convenience method that will also generate a
        ``gtoken`` if one has not already been generated, or if the user info
        has not been set. This function requires a session token to already be
        set, and will raise a ValueError if it is not. If the bullet token is
        unable to be generated, a SplatNetException will be raised.

        Raises:
            ValueError: If the session token has not been set.
            SplatNetException: If the bullet token was unable to be generated.
        """
        if TOKENS.SESSION_TOKEN not in self._tokens:
            raise ValueError(
                "Session token must be set before generating a bullet token."
            )
        if (TOKENS.GTOKEN not in self._tokens) or (self.nso._user_info is None):
            self.generate_gtoken()
        bullet_token = self.nso.get_bullet_token(
            cast(str, self.nso._gtoken), cast(dict, self.nso._user_info)
        )
        self.add_token(bullet_token, TOKENS.BULLET_TOKEN)
        bullet = self.get(TOKENS.BULLET_TOKEN, full_token=True)
        if (bullet is not None) and not bullet.is_valid:
            raise SplatNetException(
                "Bullet token was unable to be generated. This is likely due "
                "to SplatNet 3 being down. Please try again later."
            )

    def generate_all_tokens(self) -> None:
        """Generates all tokens that can be generated from the manager. This
        is a convenience method that will call the ``generate_gtoken`` and
        ``generate_bullet_token`` methods in order. This function requires a
        session token to already be set, and will raise the errors that those
        methods raise if a session token is not set.
        """
        self.logger.debug("Generating all tokens.")
        self.generate_gtoken()
        self.generate_bullet_token()

    @classmethod
    def from_session_token(cls, session_token: str) -> "TokenManager":
        """Creates a token manager from a session token.

        Given a session token, this method will create a token manager and add
        a session token to it. Additionally, it will flag the origin of the
        session token as "session_token" so that it can be saved to a config
        file later.

        Args:
            session_token (str): The session token to use to instantiate the
                ``TokenManager``.

        Returns:
            TokenManager: The token manager with the session token added.
        """
        manager = cls()
        manager.add_session_token(session_token)
        manager.flag_origin("session_token")
        return manager

    @classmethod
    def from_tokens(
        cls,
        session_token: str,
        gtoken: str | None = None,
        bullet_token: str | None = None,
    ) -> "TokenManager":
        """Creates a token manager from a session token.

        Given a session token, this method will create a token manager and add
        a session token to it. Additionally, it will flag the origin of the
        TokenManager as "tokens" so that it can be saved to a config file later.

        Args:
            session_token (str): The session token to use to instantiate the
                ``TokenManager``.
            gtoken (str | None): The gtoken to use to instantiate the
                ``TokenManager``. If not provided, a new gtoken will be
                generated. Defaults to None.
            bullet_token (str | None): The bullet token to use to instantiate
                the ``TokenManager``. If not provided, a new bullet token will
                be generated. Defaults to None.

        Returns:
            TokenManager: The token manager with the session token added.
        """
        manager = cls()
        manager.add_session_token(session_token)

        if gtoken is not None:
            manager.add_token(gtoken, TOKENS.GTOKEN)
        else:
            manager.generate_gtoken()

        if bullet_token is not None:
            manager.add_token(bullet_token, TOKENS.BULLET_TOKEN)
        else:
            manager.generate_bullet_token()

        manager.flag_origin("tokens")
        return manager

    @classmethod
    def load(cls) -> "TokenManager":
        """Loads tokens from a config file or environment variables.

        Checks for appropriate tokens in the following order:
            1. .splatnet3_scraper file
            2. Environment variables
            3. tokens.ini file

        Raises:
            ValueError: If no tokens are found.

        Returns:
            TokenManager: The token manager with the tokens loaded.
        """
        if os.path.exists(".splatnet3_scraper"):
            return cls.from_config_file(".splatnet3_scraper")
        elif any([os.environ.get(var) for var in ENV_VAR_NAMES.values()]):
            return cls.from_env()
        elif os.path.exists("tokens.ini"):
            return cls.from_config_file("tokens.ini")
        else:
            raise ValueError(
                "No tokens found. Please create a .splatnet3_scraper file, set "
                "environment variables, or create a tokens.ini file."
            )

    @classmethod
    def from_config_file(cls, path: str) -> "TokenManager":
        """Loads tokens from a config file.

        Given a path to a config file, this method will create a token manager
        and add the tokens found in the config file to it. Additionally, it
        will flag the origin of the tokens as "config_file" so that they can be
        saved to a config file later. The config file must be in the format of
        the standard ``configparser`` library, and must have a "tokens" section.
        The "tokens" section must have a "session_token" option, and may have
        "gtoken" and "bullet_token" options. An example config file is shown
        below:

        >>> [tokens]
        ... session_token = SESSION_TOKEN
        ... gtoken = GTOKEN
        ... bullet_token = BULLET_TOKEN
        ...
        ... [data]
        ... country = US
        ... language = en-US
        ...
        ... [options]
        ... user_agent = USER_AGENT

        Tests the tokens before returning the token manager using the
        ``test_tokens`` method.

        Args:
            path (str): The path to the config file.

        Raises:
            ValueError: If the config file does not have a ``tokens`` section.

        Returns:
            TokenManager: A newly created token manager with the tokens loaded
                and the origin of the token manager set to "config_file".
        """
        config = configparser.ConfigParser()
        config.read(path)
        nso = NSO.new_instance()
        tokenmanager = cls(nso)
        tokenmanager.flag_origin("config_file", path)

        if not config.has_section("tokens"):
            raise ValueError("Config file does not have a 'tokens' section.")
        for option in config.options("tokens"):
            token = config.get("tokens", option)
            if option == TOKENS.SESSION_TOKEN:
                nso._session_token = token
            elif option == TOKENS.GTOKEN:
                nso._gtoken = token
            tokenmanager.add_token(token, option)

        if not config.has_section("data"):
            tokenmanager.generate_all_tokens()
            return tokenmanager
        for option in config.options("data"):
            tokenmanager._data[option] = config.get("data", option)
        tokenmanager.test_tokens()
        return tokenmanager

    @classmethod
    def from_text_file(cls, path: str) -> "TokenManager":
        """Loads tokens from a text file, particularly s3s config files. Not
        recommended for use, but here for compatibility with s3s config files.

        Requires the text file to be a JSON file that contains a "session_token"
        key. The value of the "session_token" key will be used as the session
        token. If the text file also contains an "acc_loc" key, the value of
        the "acc_loc" key will be used to set the language and country of the
        data in the token manager.

        Tests the tokens before returning the token manager using the
        ``test_tokens`` method.

        Args:
            path (str): The path to the text file.

        Raises:
            ValueError: If the session token is not found in the JSON file.

        Returns:
            TokenManager: The token manager with the tokens loaded.
        """
        token_manager = cls()
        with open(path, "r") as f:
            data = json.load(f)

        if "session_token" not in data:
            raise ValueError("Session token not found in text file.")
        token_manager.add_session_token(data["session_token"])
        token_manager.flag_origin("text_file", path)
        if "acc_loc" in data:
            language, country = data["acc_loc"].split("|")
            token_manager._data["language"] = language
            token_manager._data["country"] = country

        if "gtoken" in data:
            token_manager.add_token(data["gtoken"], TOKENS.GTOKEN)
        if "bullettoken" in data:
            token_manager.add_token(data["bullettoken"], TOKENS.BULLET_TOKEN)
        token_manager.test_tokens()
        return token_manager

    @classmethod
    def from_env(
        cls, env_manager: EnvironmentVariablesManager | None = None
    ) -> "TokenManager":
        """Loads tokens from environment variables.

        This method will create a token manager and add the tokens found in the
        environment variables to it. The environment variables that are
        supported are:

        - SN3S_SESSION_TOKEN
        - SN3S_GTOKEN
        - SN3S_BULLET_TOKEN

        The session token environment variable is required, and if it is not
        set, a ValueError will be raised. The other environment variables are
        optional and will be generated if they are not set.

        Tests the tokens before returning the token manager using the
        ``test_tokens`` method.

        Args:
            env_manager (EnvironmentVariablesManager): The environment variables
                manager to use. If not provided, a new one will be created.

        Raises:
            ValueError: If the session token environment variable is not set.

        Returns:
            TokenManager: The token manager with the tokens loaded.
        """
        nso = NSO.new_instance()
        tokenmanager = cls(nso, env_manager=env_manager)
        tokens = tokenmanager.env_manager.get_all()
        for token, value in tokens.items():
            if token == TOKENS.SESSION_TOKEN:
                if value is None:
                    raise ValueError(
                        "Session token environment variable not set."
                    )
                nso._session_token = value
            elif value is None:
                continue
            elif token == TOKENS.GTOKEN:
                nso._gtoken = value
            tokenmanager.add_token(value, token)
        tokenmanager.flag_origin("env")
        tokenmanager.test_tokens()
        return tokenmanager

    def save(self, path: str | None = None) -> None:
        """Saves the tokens to a config file.

        Uses the ``configparser`` module to save the tokens to a config file.
        The config file will be saved to the path specified by the `path`
        argument. If the `path` argument is not specified, the config file
        will be saved to the current working directory with the name
        ``.splatnet3_scraper``. Does not consider the origin of the tokens, as
        it is assumed that this method will only be called when the user wants
        to save the tokens to disk.

        Args:
            path (str): The path to the config file.
        """
        config = configparser.ConfigParser()
        out_tokens = {}
        for token_name, token in self._tokens.items():
            out_tokens[token_name] = token.token
        config["tokens"] = out_tokens
        config["data"] = self._data
        config["metadata"] = {
            "version": __version__,
            "class": self.__class__.__name__,
        }
        if path is None:
            path = ".splatnet3_scraper"
        with open(path, "w") as configfile:
            config.write(configfile)

    def token_is_valid(self, token_type: str) -> bool:
        """Given a token type, checks if the token is valid.

        This method will check if the token is valid by checking if the token
        is expired. This method will not regenerate the token if it is invalid.
        As mentioned in the ``Token.is_valid`` property, this method will not
        check if the token is valid by making a request to the API, but rather
        checks if the token is likely to be expired by comparing the known
        expiration time of the token to the current time. If the token type is
        not found, this method will return False.

        Args:
            token_type (str): The type of token to check.

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        try:
            token = self.get(token_type, full_token=True)
        except ValueError:
            return False
        return token.is_valid

    def test_tokens(self, user_agent: str | None = None) -> None:
        """Tests the tokens.

        Checks using the ``token_is_valid`` method to see whether the tokens
        need to be regenerated. If so, the tokens will be regenerated with the
        appropriate ``generate_*`` method. Once the tokens are regenerated, it
        will make a request to the API to check if the tokens are valid. If the
        request fails, the ``generate_all_tokens`` method will be called. If the
        requests succeeds, nothing will happen. Once this method is called, the
        TokenManager can be assumed to have valid tokens and can be used to make
        requests to the API.

        Args:
            user_agent (str): The user agent to use when making the request to
                the API. If not specified, the default user agent will be used.

        Raises:
            ValueError: If the session token is not set.
        """
        if self.get(TOKENS.SESSION_TOKEN) is None:
            raise ValueError("Session Token is not set.")

        if self.token_is_valid(TOKENS.GTOKEN) is False:
            self.generate_gtoken()

        if self.token_is_valid(TOKENS.BULLET_TOKEN) is False:
            self.generate_bullet_token()

        header = queries.query_header(
            self.get(TOKENS.BULLET_TOKEN), self._data["language"], user_agent
        )

        response = requests.post(
            GRAPH_QL_REFERENCE_URL,
            data=queries.query_body("HomeQuery"),
            headers=header,
            cookies={"_gtoken": cast(str, self.get(TOKENS.GTOKEN))},
        )
        if response.status_code != 200:
            self.generate_all_tokens()

    def export_tokens(self) -> list[tuple[str, str]]:
        """Exports the tokens as a list of tuples.

        Returns:
            list[tuple[str, str]]: A list of tuples containing the token type
                and the token value.
        """
        return [
            (token_type, token.token)
            for token_type, token in self._tokens.items()
        ]
