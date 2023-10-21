import math
import time

import freezegun

from splatnet3_scraper.auth.tokens.tokens import Token

test_date_str = "2023-01-01 00:00:00"


def mock_token(token_name: str) -> Token:
    with freezegun.freeze_time(test_date_str):
        return Token(token_name, token_name, time.time())


class TestToken:
    @freezegun.freeze_time("2023-01-01 00:00:00")
    def test_new_token(self):
        timestamp = time.time()
        token = Token("test", "test_name", timestamp)
        assert token.value == "test"
        assert token.name == "test_name"
        assert token.timestamp == timestamp
        assert math.isclose(token.expiration, timestamp + 1e10)

    @freezegun.freeze_time("2023-01-01 00:00:00")
    def test_properties(self):
        token = mock_token("test")
        assert token.is_expired is False
        assert token.is_valid is True
        assert math.isclose(token.time_left, 1e10)
        assert token.time_left_str == "basically forever"

        token = mock_token("gtoken")
        assert token.time_left_str == "6h 30m"
        with freezegun.freeze_time("2023-01-01 06:00:00") as frozen_time:
            assert token.time_left_str == "30m"

            frozen_time.tick(10 * 60 + 5)
            assert token.time_left_str == "19m 55.0s"

            frozen_time.tick(20 * 60)
            assert token.time_left_str == "Expired"

    @freezegun.freeze_time("2023-01-01 00:00:00")
    def test_repr(self):
        token = mock_token("test")
        spaces = " " * len("Token(")
        expected = (
            "Token("
            + "value=test...,\n"
            + spaces
            + "name=test,\n"
            + spaces
            + "expires in basically forever"
            + "\n)"
        )
        assert repr(token) == expected
