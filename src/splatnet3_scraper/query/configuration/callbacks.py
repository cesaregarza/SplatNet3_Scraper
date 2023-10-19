import re

delimiter = re.compile(r"\s*\,\s*")


# Make sure all callbacks return values, even if they are not transformed.
def session_token_callback(
    session_token: str | None,
) -> str:
    if session_token is None:
        raise ValueError("Session token must be provided.")
    return session_token


def f_token_url_callback(f_token_url: str | list[str] | None) -> list[str]:
    if f_token_url is None:
        raise ValueError("F token URL must be provided.")
    elif isinstance(f_token_url, list):
        return f_token_url
    else:
        return delimiter.split(f_token_url)


def f_token_url_save_callback(f_token_url: list[str] | None) -> str:
    if f_token_url is None:
        raise ValueError("F token URL must be provided.")
    return ",".join(f_token_url)


def log_level_callback(log_level: str | None) -> str:
    # Does not set the log level, just checks that it is valid
    if log_level is None:
        return "INFO"
    try:
        log_level = log_level.upper()
        assert log_level in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
        return log_level
    except AssertionError:
        raise ValueError(
            "Log level must be one of CRITICAL, ERROR, WARNING, INFO, DEBUG"
        ) from None
