from __future__ import annotations

import os
from typing import Any, Callable


class ConfigOption:
    """Represents a single configuration option in the system.

    Each ConfigOption instance contains information about a particular
    configuration parameter. It will contain the name of the option, the
    default value, the deprecated names, the deprecated section, the callback
    function, the section, the environment variable name, and the environment
    variable prefix. It also contains the value of the option, which can be
    set and retrieved using the set_value and get_value methods. This class also
    will attempt to get the value from the environment variable if it is set.
    """

    def __init__(
        self,
        name: str,
        default: Any = None,
        deprecated_names: list[str] | str | None = None,
        deprecated_section: str | None = None,
        callback: Callable[[str | None], Any] | None = None,
        section: str = "Options",
        env_var: str | None = None,
        env_prefix: str | None = None,
    ) -> None:
        """Initializes the class.

        Args:
            name (str): The name of the option.
            default (Any): The default value of the option. If None, the option
                does not have a default value. Defaults to None.
            deprecated_names (list[str] | str | None): The deprecated names of
                the option. If None, the option does not have any deprecated
                names. If a string is provided, it will be converted to a list
                with one element. These names will be used to look up the
                option, but the new name will be used for any output. Defaults
                to None.
            deprecated_section (str | None): The deprecated section of the
                option. This should be used if the option was moved to a
                different section. If None, the option will be assumed to be in
                the same section. Defaults to None.
            callback (Callable[[str  |  None], Any] | None): The callback
                function to call when the option's value is set. It should take
                one argument, the new value, and should return the new value,
                with any modifications. If the callback function returns None,
                it will act as a verification function. If the callback
                function raises an exception, the value will not be set. If
                None, no callback function will be used. Defaults to None.
            section (str): The section of the option. Defaults to "Options".
            env_var (str | None): The environment variable to use for the
                option. If None, no environment variable will be used. This will
                be the base name of the variable. For example, if the name of
                the option is "TEST", the environment variable will be
                "TEST". Higher level functions may add a prefix to the
                environment variable, so if the name of the set prefix is
                "PREFIX", the environment variable will be "PREFIX_TEST".
                Defaults to None.
            env_prefix (str | None): The prefix to use for the environment
                variable. If None, no prefix will be used. Defaults to None.
        """
        self.name = name
        self.default = default
        self.deprecated_names = deprecated_names
        self.deprecated_section = deprecated_section
        self.callback = callback
        self.section = section
        self.env_var = env_var
        self.env_prefix = env_prefix
        self.value: str | None = None

    @property
    def env_key(self) -> str | None:
        """The environment variable key.

        Returns the environment variable key. This is the environment variable
        name with the prefix added to it.

        Returns:
            str | None: The environment variable key.
        """
        if self.env_var is None:
            return None
        elif self.env_prefix is None:
            return self.env_var
        else:
            return f"{self.env_prefix}_{self.env_var}"

    def set_value(self, value: str | None) -> None:
        """Sets the value of the option.

        If the option has a callback function, it will be called with the new
        value as an argument known as the "original value". If the callback
        function returns a value, it will be used as the new value known as the
        "returned value". If the callback function returns None, the original
        value will be used as the new value. If the callback function raises an
        exception, the value will not be set. If the value is None and the
        option has a default value, the default value will be used as the new
        value.

        Args:
            value (str | None): The new value of the option.
        """
        if (self.callback is not None) and (value is not None):
            value = self.callback(value)
        self.value = value or self.default

    def get_value(self) -> str | None:
        """Gets the value of the option. It will go through the following steps
        to get the value:

        1. If the value is set, return it.
        2. If the option has an environment variable name, attempt to get the
           value from the environment variable.
        3. If the option has a default value, return it.
        4. If none of the above are true, raise a ValueError.

        Raises:
            ValueError: If no value is set, it wasn't able to get the value
                from the environment variable, and the option doesn't have a
                default value.

        Returns:
            str | None: The value of the option.
        """
        if self.value is not None:
            return self.value
        elif self.env_key is not None and (value := os.getenv(self.env_key)):
            self.set_value(value)
            return value
        elif self.default is not None:
            return self.default
        else:
            raise ValueError("No value set for option")

    def set_prefix(self, prefix: str) -> None:
        """Sets the prefix for the environment variable.

        Args:
            prefix (str): The prefix to use for the environment variable.
        """
        self.env_prefix = prefix
