import time

from s3s_express.constants import TOKEN_EXPIRATIONS
from s3s_express.tokens.nso import NSO


class Token:
    def __init__(self, token: str, token_type: str, timestamp: float) -> None:
        self.token = token
        self.token_type = token_type
        self.timestamp = timestamp
        self.expiration = TOKEN_EXPIRATIONS[token_type] + timestamp

    @property
    def is_expired(self) -> bool:
        return self.time_left <= 0

    @property
    def time_left(self) -> float:
        return self.expiration - time.time()

    @property
    def time_left_str(self) -> str:
        time_left = self.time_left
        mins, secs = divmod(time_left, 60)
        hours, mins = divmod(mins, 60)

        out = ""
        if hours > 0:
            out += f"{hours}h "
        if mins > 0:
            out += f"{mins}m "
        if secs > 0:
            out += f"{secs}s"
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
    def __init__(self, nso: NSO) -> None:
        self.nso = nso
        self._tokens = {}

    def add_token(
        self,
        token: str | Token,
        token_type: str | None = None,
        timestamp: float | None = None,
    ) -> None:
        if isinstance(token, Token):
            self._tokens[token.token_type] = token
            return
        if token_type is None:
            raise ValueError("token_type must be provided if token is a str.")
        if timestamp is None:
            timestamp = time.time()
        self._tokens[token_type] = Token(token, token_type, timestamp)

    def generate_gtoken(self) -> None:
        if "session_token" not in self._tokens:
            raise ValueError(
                "Session token must be set before generating a gtoken."
            )
        gtoken = self.nso.get_gtoken(self.nso.session_token)
        self.add_token(gtoken, "gtoken")

    def generate_bullet_token(self) -> None:
        if "session_token" not in self._tokens:
            raise ValueError(
                "Session token must be set before generating a bullet token."
            )
        if "gtoken" not in self._tokens:
            self.generate_gtoken()
        bullet_token = self.nso.get_bullet_token(self.nso.session_token)
        self.add_token(bullet_token, "bullet_token")

    