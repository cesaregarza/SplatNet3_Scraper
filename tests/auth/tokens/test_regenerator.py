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
base_regen_path = "splatnet3_scraper.auth.tokens.regenerator"
regen_path = base_regen_path + ".TokenRegenerator"


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

    @pytest.mark.parametrize(
        "with_gtoken",
        [True, False],
        ids=["with_gtoken", "without_gtoken"],
    )
    @freezegun.freeze_time(test_date_str)
    def test_generate_bullet_token(self, with_gtoken: bool) -> None:
        nso = MagicMock()
        if with_gtoken:
            nso._user_info = {"test": "test"}
            nso._gtoken = "test_gtoken"
        else:
            nso._user_info = None

        test_gtoken = MagicMock()
        test_gtoken.value = "test_gtoken"
        with (
            patch(regen_path + ".generate_gtoken") as mock_generate_gtoken,
            patch(base_regen_path + ".Token") as mock_token,
        ):
            mock_generate_gtoken.return_value = test_gtoken
            nso.get_bullet_token.return_value = "test_bullet_token"
            TokenRegenerator.generate_bullet_token(nso, self.ftokens_url)
            if with_gtoken:
                mock_generate_gtoken.assert_not_called()
                mock_token.assert_called_once_with(
                    "test_bullet_token",
                    TOKENS.BULLET_TOKEN,
                    time.time(),
                )
            else:
                mock_generate_gtoken.assert_called_once_with(
                    nso, self.ftokens_url
                )
                mock_token.assert_called_once_with(
                    "test_bullet_token",
                    TOKENS.BULLET_TOKEN,
                    time.time(),
                )
