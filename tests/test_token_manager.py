import time

import freezegun
import pytest

from splatnet3_scraper.base.tokens.token_manager import Token, TokenManager
from splatnet3_scraper.constants import (
    ENV_VAR_NAMES,
    GRAPH_QL_REFERENCE_URL,
    TOKEN_EXPIRATIONS,
    TOKENS,
)

@freezegun.freeze_time("2021-01-01 00:00:00")
def mock_token(token_type):
    return Token(token_type, token_type, time.time())


class TestToken:
    @freezegun.freeze_time("2021-01-01 00:00:00")
    def test_new_token(self):
        timestamp = time.time()
        token = Token("test", "test_type", timestamp)
        assert token.token == "test"
        assert token.token_type == "test_type"
        assert token.timestamp == timestamp
        assert token.expiration == timestamp + 1e10
    
    @freezegun.freeze_time("2021-01-01 00:00:00")
    def test_properties(self):
        token = mock_token("test")
        assert token.is_expired is False
        assert token.is_valid is True
        assert token.time_left == 1e10
        assert token.time_left_str == "basically forever"
        
        token = mock_token("gtoken")
        assert token.time_left_str == "6h 30m"
    
    @freezegun.freeze_time("2021-01-01 00:00:00")
    def test_repr(self):
        token = mock_token("test")
        spaces = " " * len("Token(")
        expected = (
            "Token("
            + "token=test...,\n"
            + spaces
            + "type=test,\n"
            + spaces
            + "expires in basically forever"
            + "\n)"
        )
        assert repr(token) == expected
