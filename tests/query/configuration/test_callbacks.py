from unittest.mock import MagicMock, patch

import pytest

from splatnet3_scraper.query.configuration.callbacks import (
    f_token_url_callback,
    log_level_callback,
    session_token_callback,
)


class TestCallbacks:
    @pytest.mark.parametrize(
        "session_token",
        [
            "session_token",
            None,
        ],
        ids=[
            "valid",
            "invalid",
        ],
    )
    def test_session_token_callback(self, session_token: str | None) -> None:
        if session_token is None:
            with pytest.raises(ValueError):
                session_token_callback(session_token)
        else:
            assert session_token_callback(session_token) == session_token

    @pytest.mark.parametrize(
        "f_token_url, expected",
        [
            ("f_token_url", ["f_token_url"]),
            ("f_token_url_1,f_token_url_2", ["f_token_url_1", "f_token_url_2"]),
            (["f_token_url"], ["f_token_url"]),
            (None, None),
        ],
        ids=[
            "valid",
            "valid comma separated",
            "valid list",
            "invalid",
        ],
    )
    def test_f_token_url_callback(
        self, f_token_url: str | list[str] | None, expected: list[str] | None
    ) -> None:
        if f_token_url is None:
            with pytest.raises(ValueError):
                f_token_url_callback(f_token_url)
        else:
            assert f_token_url_callback(f_token_url) == expected

    @pytest.mark.parametrize(
        "log_level, expected",
        [
            ("CRITICAL", "CRITICAL"),
            ("ERROR", "ERROR"),
            ("WARNING", "WARNING"),
            ("INFO", "INFO"),
            ("DEBUG", "DEBUG"),
            (None, "INFO"),
            ("invalid", None),
        ],
        ids=[
            "CRITICAL",
            "ERROR",
            "WARNING",
            "INFO",
            "DEBUG",
            "default",
            "invalid",
        ],
    )
    def test_log_level_callback(
        self, log_level: str | None, expected: str | None
    ) -> None:
        if log_level == "invalid":
            with pytest.raises(ValueError):
                log_level_callback(log_level)
        else:
            assert log_level_callback(log_level) == expected
