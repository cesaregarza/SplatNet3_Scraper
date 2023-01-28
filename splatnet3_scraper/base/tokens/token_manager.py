import configparser
import os
import re
import time
from typing import Literal, cast, overload

import requests

from splatnet3_scraper import __version__
from splatnet3_scraper.base.graph_ql_queries import queries
from splatnet3_scraper.base.tokens.nso import (
    NSO,
    NintendoException,
    SplatnetException,
)
from splatnet3_scraper.constants import (
    ENV_VAR_NAMES,
    GRAPH_QL_REFERENCE_URL,
    TOKEN_EXPIRATIONS,
    TOKENS,
)
from splatnet3_scraper.utils import retry

text_config_re = re.compile(r"\s*=*\s*")


class Token:
    """Represents at token. Contains the token itself, the type of token, and
    the time it was created. Can be used to check if the token is expired or
    display the time left before it expires.
    """

    def __init__(self, token: str, token_type: str, timestamp: float) -> None:
        self.token = token
        self.token_type = token_type
        self.timestamp = timestamp
        self.expiration = TOKEN_EXPIRATIONS.get(token_type, 1e10) + timestamp

    @property
    def is_valid(self) -> bool:
        return (self.token is not None) and (self.token != "")

    @property
    def is_expired(self) -> bool:
        return self.time_left <= 0

    @property
    def time_left(self) -> float:
        return self.expiration - time.time()

    @property
    def time_left_str(self) -> str:
        """Returns a string representation of the time left before the token
        expires. If the token is expired, "Expired" will be returned.

        Returns:
            str: A string representation of the time left before the token
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
    """Manages tokens. Can be used to add tokens, generate tokens from the NSO
    class, check if tokens are expired, load tokens from a config file or
    environment variables, save tokens to a config file, and display the time
    left before tokens expire.
    """

    def __init__(self, nso: NSO | None = None) -> None:
        nso = nso if nso is not None else NSO.new_instance()
        self.nso = nso
        self._tokens: dict[str, Token] = {}
        self._data: dict[str, str] = {}

    def flag_origin(self, origin: str, data: str | None = None) -> None:
        """Flags the origin of the token manager. This is used to determine
        whether the token manager was loaded from a config file or environment
        variables.

        Args:
            origin (str): The origin of the token manager.
            data (str | None): Additional data about the origin. For example,
                if the token manager was loaded from a config file, this would
                be the path to the config file. On the other hand, if the token
                manager was loaded from environment variables, this would be
                None.
        """
        self._origin = {"origin": origin, "data": data}

    def add_token(
        self,
        token: str | Token,
        token_type: str | None = None,
        timestamp: float | None = None,
    ) -> None:
        """Adds a token to the manager. If the token is a string, the token
        type must be provided. If the token is a Token object, the object will
        be added to the manager.

        Args:
            token (str | Token): The token to add.
            token_type (str | None): The type of token. If token is an instance
                of Token, this will be ignored. If token is a string, this must
                be provided.
            timestamp (float | None): The time the token was created. If not
                provided, the current time will be used.

        Raises:
            ValueError: If token is a string and token_type is not provided.
        """
        if isinstance(token, Token):
            self._tokens[token.token_type] = token
            return
        if token_type is None:
            raise ValueError("token_type must be provided if token is a str.")
        if timestamp is None:
            timestamp = time.time()
        self._tokens[token_type] = Token(token, token_type, timestamp)

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
        """Gets a token from the manager. If full_token is True, the Token
        object will be returned. Otherwise, the token string will be returned.

        Args:
            token_type (str): The type of token to get.
            full_token (bool): Whether to return the full Token object or just
                the token string.

        Raises:
            ValueError: If the token type is not found.

        Returns:
            str | Token: The token or Token object.
        """
        token_obj = self._tokens.get(token_type, None)
        if token_obj is None:
            raise ValueError(f"Token of type {token_type} not found.")
        if full_token:
            return token_obj
        return token_obj.token

    @property
    def data(self) -> dict[str, str]:
        """Returns the data stored in the manager.

        Returns:
            dict[str, str]: The data stored in the manager.
        """
        return self._data

    def add_session_token(self, token: str) -> None:
        """Adds a session token to the manager.

        Args:
            token (str): The session token to add.
        """
        self.add_token(token, TOKENS.SESSION_TOKEN)
        self.nso._session_token = token

    def generate_gtoken(self) -> None:
        """Generates a gtoken from the NSO class and adds it to the manager.
        Requires a session token to already be set.

        Raises:
            ValueError: If the session token has not been set.
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

    @retry(times=1, exceptions=SplatnetException)
    def generate_bullet_token(self) -> None:
        """Generates a bullet token from the NSO class and adds it to the
        manager. If a gtoken has not been generated, one will be generated
        before generating the bullet token. Requires a session token to already
        be set.

        Raises:
            ValueError: If the session token has not been set.
            SplatnetException: If the bullet token was unable to be generated.
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
            raise SplatnetException(
                "Bullet token was unable to be generated. This is likely due "
                "to SplatNet 3 being down. Please try again later."
            )

    def generate_all_tokens(self) -> None:
        """Generates all tokens from the NSO class and adds them to the
        manager. Requires a session token to already be set.
        """
        self.generate_gtoken()
        self.generate_bullet_token()

    @classmethod
    def from_session_token(cls, session_token: str) -> "TokenManager":
        """Creates a token manager from a session token.

        Args:
            session_token (str): The session token to use.

        Returns:
            TokenManager: The token manager with the session token added.
        """
        manager = cls()
        manager.add_session_token(session_token)
        manager.flag_origin("session_token")
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

        Args:
            path (str): The path to the config file.

        Raises:
            ValueError: If the config file does not have a 'tokens' section.

        Returns:
            TokenManager: The token manager with the tokens loaded.
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
        """Loads tokens from a text file. Not recommended, but here for
        compatability with s3s config files.

        Args:
            path (str): The path to the text file.

        Returns:
            TokenManager: The token manager with the tokens loaded.
        """
        token_manager = cls()
        with open(path, "r") as f:
            lines = f.readlines()
        # Clean up the lines
        for line in lines:
            stripped_line = line.strip()
            token_name, token = text_config_re.split(stripped_line)
            if token_name == TOKENS.SESSION_TOKEN:
                token_manager.add_session_token(token)
            else:
                token_manager.add_token(token, token_name)
        token_manager.flag_origin("text_file", path)
        token_manager.test_tokens()
        return token_manager

    @classmethod
    def from_env(cls) -> "TokenManager":
        """Loads tokens from environment variables.

        Raises:
            ValueError: If the session token environment variable is not set.

        Returns:
            TokenManager: The token manager with the tokens loaded.
        """
        nso = NSO.new_instance()
        tokenmanager = cls(nso)
        for token in ENV_VAR_NAMES:
            token_env = os.environ.get(ENV_VAR_NAMES[token])
            if token == TOKENS.SESSION_TOKEN:
                if token_env is None:
                    raise ValueError(
                        "Session token environment variable not set."
                    )
                tokenmanager.nso._session_token = token_env
            elif token_env is None:
                continue
            elif token == TOKENS.GTOKEN:
                tokenmanager.nso._gtoken = token_env
            tokenmanager.add_token(token_env, token)
        tokenmanager.flag_origin("env")
        tokenmanager.test_tokens()
        return tokenmanager

    def save(self, path: str | None = None) -> None:
        """Saves the tokens to a config file.

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
        """Checks if a token is valid.

        Args:
            token_type (str): The type of token to check.

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        token = self.get(token_type, full_token=True)
        if token is None:
            return False
        return token.is_valid

    def test_tokens(self, user_agent: str | None = None) -> None:
        """Tests the tokens by making a request to the GraphQL endpoint and
        regenerate tokens if they are invalid.

        Args:
            user_agent (str): The user agent to use for the request.

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
