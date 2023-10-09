import logging


def session_token_callback(
    session_token: str | None,
) -> None:
    if session_token is None:
        raise ValueError("Session token must be provided.")


def log_level_callback(log_level: str | None) -> None:
    # Does not set the log level, just checks that it is valid
    if log_level is None:
        return
    try:
        log_level = log_level.upper()
        assert log_level in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
    except AssertionError:
        raise ValueError(
            "Log level must be one of CRITICAL, ERROR, WARNING, INFO, DEBUG"
        ) from None
