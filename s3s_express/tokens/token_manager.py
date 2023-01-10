import configparser
import os
import time

from s3s_express.constants import ENV_VAR_NAMES, TOKEN_EXPIRATIONS, TOKENS
from s3s_express.tokens.nso import NSO


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
        return out

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

    def generate_bullet_token(self) -> None:
        """Generates a bullet token from the NSO class and adds it to the
        manager. If a gtoken has not been generated, one will be generated
        before generating the bullet token. Requires a session token to already
        be set.

        Raises:
            ValueError: If the session token has not been set.
        """
        if TOKENS.SESSION_TOKEN not in self._tokens:
            raise ValueError(
                "Session token must be set before generating a bullet token."
            )
        if TOKENS.GTOKEN not in self._tokens:
            self.generate_gtoken()
        bullet_token = self.nso.get_bullet_token(
            self.nso._gtoken, self.nso._user_info
        )
        self.add_token(bullet_token, TOKENS.BULLET_TOKEN)

    @staticmethod
    def load() -> "TokenManager":
        """Loads tokens from a config file or environment variables.

        Checks for appropriate tokens in the following order:
            1. .s3s_express file
            2. Environment variables
            3. tokens.ini file

        Raises:
            ValueError: If no tokens are found.

        Returns:
            TokenManager: The token manager with the tokens loaded.
        """
        if os.path.exists(".s3s_express"):
            return TokenManager.from_path(".s3s_express")
        elif any([os.environ.get(var) for var in ENV_VAR_NAMES.values()]):
            return TokenManager.from_env()
        elif os.path.exists("tokens.ini"):
            return TokenManager.from_path("tokens.ini")
        else:
            raise ValueError(
                "No tokens found. Please create a .s3s_express file, set "
                "environment variables, or create a tokens.ini file."
            )

    @staticmethod
    def from_path(path: str) -> "TokenManager":
        """Loads tokens from a config file.

        Args:
            path (str): The path to the config file.

        Returns:
            TokenManager: The token manager with the tokens loaded.
        """
        config = configparser.ConfigParser()
        config.read(path)
        nso = NSO.new_instance()
        tokenmanager = TokenManager(nso)
        for option in config.options("tokens"):
            token = config.get("tokens", option)
            if option == TOKENS.SESSION_TOKEN:
                nso._session_token = token
            elif option == TOKENS.GTOKEN:
                nso._gtoken = token
            tokenmanager.add_token(token, option)
        return tokenmanager

    @staticmethod
    def from_env() -> "TokenManager":
        """Loads tokens from environment variables.

        Returns:
            TokenManager: The token manager with the tokens loaded.
        """
        nso = NSO.new_instance()
        tokenmanager = TokenManager(nso)
        for token in ENV_VAR_NAMES:
            token_env = os.environ.get(ENV_VAR_NAMES[token])
            if token_env is None:
                continue
            if token == TOKENS.SESSION_TOKEN:
                tokenmanager.nso._session_token = token_env
            elif token == TOKENS.GTOKEN:
                tokenmanager.nso._gtoken = token_env
            tokenmanager.add_token(token_env, token)
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
        if path is None:
            path = ".s3s_express"
        with open(path, "w") as configfile:
            config.write(configfile)
