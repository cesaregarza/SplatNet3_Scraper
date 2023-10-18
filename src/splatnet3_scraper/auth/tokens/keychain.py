from __future__ import annotations

import logging
import time
from typing import Literal, overload

from splatnet3_scraper.auth.tokens.tokens import Token

logger = logging.getLogger(__name__)


class TokenKeychain:
    """Class that represents a keychain of tokens. This class is meant to store
    tokens and provide convenience methods for getting all sorts of metadata
    about the tokens. It also provides methods for adding, removing, and
    updating tokens in the keychain.
    """

    def __init__(self) -> None:
        """Initializes a ``TokenKeychain`` object. The keychain is initialized
        as an empty dictionary.
        """
        self._keychain: dict[str, Token] = {}

    @property
    def keychain(self) -> dict[str, Token]:
        """The keychain of tokens.

        Returns:
            dict[str, Token]: The keychain of tokens.
        """
        return self._keychain

    @keychain.setter
    def keychain(self, keychain: dict[str, Token]) -> None:
        """Sets the keychain of tokens.

        Args:
            keychain (dict[str, Token]): The keychain of tokens.
        """
        self._keychain = keychain

    @classmethod
    def from_dict(cls, keychain: dict[str, Token]) -> TokenKeychain:
        """Creates a ``TokenKeychain`` object from a dictionary. This is useful
        for loading a keychain from a file.

        Args:
            keychain (dict[str, Token]): The dictionary to create the keychain
                from.

        Returns:
            TokenKeychain: The ``TokenKeychain`` object created from the
                dictionary.
        """
        token_keychain = cls()
        token_keychain.keychain = keychain
        return token_keychain

    @classmethod
    def from_list(cls, tokens: list[Token]) -> TokenKeychain:
        """Creates a ``TokenKeychain`` object from a list. This is useful for
        loading a keychain from a file.

        Args:
            tokens (list[Token]): The list to create the keychain from.

        Returns:
            TokenKeychain: The ``TokenKeychain`` object created from the list.
        """
        token_keychain = cls()
        token_keychain.keychain = {token.name: token for token in tokens}
        return token_keychain

    def to_dict(self) -> dict[str, str]:
        """Converts the keychain to a dictionary. This is useful for saving the
        keychain to a file.

        Returns:
            dict[str, str]: The keychain as a dictionary.
        """
        return {name: token.value for name, token in self.keychain.items()}

    @overload
    def get(self, name: str, full_token: Literal[False] = ...) -> str:
        ...

    @overload
    def get(self, name: str, full_token: Literal[True]) -> Token:
        ...

    @overload
    def get(self, name: str, full_token: bool) -> str | Token:
        ...

    def get(self, name: str, full_token: bool = False) -> str | Token:
        """Gets a token from the manager given a token type.

        If ``full_token`` is True, the full ``Token`` object will be returned.
        Otherwise, just the value of the token will be returned. If the token
        type is not found, a ValueError will be raised.

        Args:
            name (str): The type of the token to get, as defined in the
                ``Token.name`` field.
            full_token (bool): Whether to return the full ``Token`` object or
                just the value of the token. Defaults to False.

        Raises:
            ValueError: If the given token type is not found in the manager.

        Returns:
            str | Token: The token, either as a string or a ``Token`` object as
                defined by the ``full_token`` argument.
        """
        token_obj = self.keychain.get(name, None)
        if token_obj is None:
            raise ValueError(f"Token named {name} not found.")
        if full_token:
            return token_obj
        return token_obj.value

    @staticmethod
    def generate_token(
        name: str, value: str, timestamp: float | None = None
    ) -> Token:
        """Generates a token object from a name and value.

        Args:
            name (str): The name of the token.
            value (str): The value of the token.
            timestamp (float, optional): The timestamp of the token. Defaults to
                None.

        Returns:
            Token: The token object.
        """
        if timestamp is None:
            timestamp = time.time()
        return Token(value, name, timestamp)

    def add_token(
        self,
        token: str | Token,
        token_name: str | None = None,
        timestamp: float | None = None,
    ) -> Token:
        """Adds a token to the keychain. If the token is a string, the name of
        the token must be provided. If the token is a ``Token`` object, the
        name of the token will be used. If the token already exists, it will
        overwrite the existing token.

        Args:
            token (str | Token): The token to add to the keychain.
            token_name (str | None, optional): The name of the token. Only
                required if the token is a string. Defaults to None.
            timestamp (float | None, optional): The timestamp of the token.
                Defaults to None.

        Raises:
            ValueError: If the token is a string and the name of the token is
                not provided.

        Returns:
            Token: The token that was added to the keychain. This is useful if
                the token was generated from a string, as the timestamp will be
                set to the current time.
        """
        if isinstance(token, str):
            if token_name is None:
                raise ValueError(
                    "token_name must be provided if token is a string."
                )
            token = self.generate_token(token_name, token, timestamp)

        logger.info("Adding token %s", token.name)
        self.keychain[token.name] = token
        return token
