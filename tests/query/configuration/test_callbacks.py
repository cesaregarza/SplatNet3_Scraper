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
