import time

from splatnet3_scraper.constants import TOKEN_EXPIRATIONS


class Token:
    """Class that represents a token. This class is meant to store the token
    itself, the type of token it is, and the time it was created. It can be used
    to check if the token is expired or display the time left before it expires.
    It also provides convenience methods for getting all sorts of metadata about
    the token.
    """

    def __init__(self, value: str, name: str, timestamp: float) -> None:
        """Initializes a ``Token`` object. The expiration time is calculated
        based on the token type, with a default of ``1e10`` seconds (about 316
        days, this should be basically forever for all intents and purposes; if
        you have a python session running for that long, you have bigger
        problems than a token expiring).

        Args:
            value (str): The value of the token, this is the actual token.
            name (str): The name of the token, this is used to identify which
                type of token it represents, making it easier for the manager
                to handle the tokens when searching for a specific one. It also
                determines the expiration time of the token.
            timestamp (float): The time the token was created, in seconds since
                the epoch. This is used to determine if the token is expired.
        """
        self.value = value
        self.name = name
        self.timestamp = timestamp
        self.expiration = TOKEN_EXPIRATIONS.get(name, 1e10) + timestamp

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
        return (self.value is not None) and (self.value != "")

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
            f"value={self.value[:5]}...,\n"
            + spaces
            + f"name={self.name},\n"
            + spaces
            + "expires in "
            + self.time_left_str
            + "\n)"
        )
        return out
