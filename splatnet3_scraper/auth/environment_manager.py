import os

from splatnet3_scraper.constants import ENV_VAR_NAMES, TOKENS


class EnvironmentVariablesManager:
    """Manages environment variables for the scraper.

    This class is used to manage the environment variables in an easy way. Any
    environment variable calls should be done through this class, it will handle
    obtaining the environment variables, allow additional environment variables
    to be added and defined, and will also handle the base environment variables
    that are required for this package to work.
    """

    BASE_TOKENS = [TOKENS.SESSION_TOKEN, TOKENS.GTOKEN, TOKENS.BULLET_TOKEN]

    def __init__(self) -> None:
        """Initializes the class and sets up the base environment variables."""
        self.variable_names = {}
        for token in self.BASE_TOKENS:
            self.variable_names[token] = ENV_VAR_NAMES[token]

    def token_to_variable(self, token: str) -> str:
        """Given the token name, returns the environment variable name.

        Args:
            token (str): The token name.

        Returns:
            str: The environment variable name.
        """
        return self.variable_names[token]

    def variable_to_token(self, variable: str) -> str:
        """Given the environment variable name, returns the token name.

        Args:
            variable (str): The environment variable name.

        Raises:
            KeyError: If the variable is not defined.

        Returns:
            str: The token name.
        """
        for token, variable_name in self.variable_names.items():
            if variable_name == variable:
                return token
        raise KeyError(f"Variable {variable} is not defined.")

    def add_token(self, token_name: str, variable_name: str) -> None:
        """Adds a new token to the environment variables.

        Args:
            token_name (str): The token name.
            variable_name (str): The environment variable name.
        """
        self.variable_names[token_name] = variable_name

    def remove_token(self, token_name: str) -> None:
        """Removes a token from the environment variables.

        Args:
            token_name (str): The token name.

        Raises:
            ValueError: If the token is a base token.
        """
        if token_name in self.BASE_TOKENS:
            raise ValueError(f"Cannot remove base token {token_name}.")
        del self.variable_names[token_name]

    def get(self, token: str) -> str | None:
        """Gets the environment variable for the given token.

        Args:
            token (str): The token to get the environment variable for.

        Returns:
            str | None: The environment variable, or None if it is not set.
        """
        return os.environ.get(self.token_to_variable(token))

    def get_all(self) -> dict[str, str | None]:
        """Gets all the environment variables.

        Returns:
            dict[str, str]: The environment variables.
        """
        return {token: self.get(token) for token in self.variable_names.keys()}
