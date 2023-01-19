import pytest
import freezegun
import time

from splatnet3_scraper.base.tokens.token_manager import Token, TokenManager
from splatnet3_scraper.constants import (
    ENV_VAR_NAMES,
    GRAPH_QL_REFERENCE_URL,
    TOKEN_EXPIRATIONS,
    TOKENS
)

class TestToken:
    @freezegun.freeze_time("2021-01-01 00:00:00")
    def test_new_token(self):
        timestamp = time.time()
        token = Token("test", "test_type", timestamp)
        assert token.token == "test"
        assert token.token_type == "test_type"
        assert token.timestamp == timestamp
        assert token.expiration == timestamp + 1e10