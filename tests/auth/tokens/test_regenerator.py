import time
from unittest.mock import MagicMock, patch

import freezegun
import pytest
import requests

from splatnet3_scraper.auth.exceptions import FTokenException, SplatNetException
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.auth.tokens.regenerator import TokenRegenerator
from splatnet3_scraper.auth.tokens.tokens import Token
from splatnet3_scraper.constants import (
    DEFAULT_USER_AGENT,
    GRAPH_QL_REFERENCE_URL,
    TOKENS,
)

test_date_str = "2023-01-01 00:00:00"


class TestTokenRegenerator:

    ftokens_url = [
        "test_url_1",
        "test_url_2",
        "test_url_3",
        "test_url_4",
    ]

    @pytest.mark.parametrize(
        "first_ftoken_pass_idx",
        [0, 1, 2, 3, 4],
        ids=["first_pass", "second_pass", "third_pass", "fourth_pass", "fail"],
    )
    @freezegun.freeze_time(test_date_str)
    def test_generate_gtoken(self, first_ftoken_pass_idx: int) -> None:
        nso = MagicMock()
        count = 0

        def mock_get_gtoken(*args) -> str:
            nonlocal count
            if count == first_ftoken_pass_idx:
                return "test_gtoken"
            else:
                count += 1
                raise FTokenException("test")

        nso.get_gtoken.side_effect = mock_get_gtoken
        if first_ftoken_pass_idx == 4:
            with pytest.raises(FTokenException):
                TokenRegenerator.generate_gtoken(nso, self.ftokens_url)
        else:
            gtoken = TokenRegenerator.generate_gtoken(nso, self.ftokens_url)
            assert gtoken.value == "test_gtoken"
            assert gtoken.name == TOKENS.GTOKEN
            assert gtoken.timestamp == time.time()
