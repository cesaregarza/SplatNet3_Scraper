import time
from unittest.mock import MagicMock, patch

import freezegun
import pytest

from splatnet3_scraper.auth.exceptions import FTokenException
from splatnet3_scraper.auth.tokens.regenerator import TokenRegenerator
from splatnet3_scraper.constants import (
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

    def test_generate_all_tokens(self) -> None:
        nso = MagicMock()
        with (
            patch(regen_path + ".generate_gtoken") as mock_gtoken,
            patch(regen_path + ".generate_bullet_token") as mock_bullet,
        ):
            mock_gtoken.return_value = "test_gtoken"
            expected = TokenRegenerator.generate_all_tokens(
                nso, self.ftokens_url, "test_user_agent"
            )
            mock_gtoken.assert_called_once_with(nso, self.ftokens_url)
            mock_bullet.assert_called_once_with(
                nso, self.ftokens_url, "test_user_agent"
            )

            assert expected == {
                TOKENS.GTOKEN: "test_gtoken",
                TOKENS.BULLET_TOKEN: mock_bullet.return_value,
            }

    @pytest.mark.parametrize(
        "valid_gtoken",
        [True, False],
        ids=["valid_gtoken", "invalid_gtoken"],
    )
    @pytest.mark.parametrize(
        "valid_bullet",
        [True, False],
        ids=["valid_bullet", "invalid_bullet"],
    )
    @pytest.mark.parametrize(
        "valid_response",
        [True, False],
        ids=["valid_response", "invalid_response"],
    )
    def test_validate_tokens(
        self, valid_gtoken: bool, valid_bullet: bool, valid_response: bool
    ) -> None:
        nso = MagicMock()
        gtoken = MagicMock()
        bullet_token = MagicMock()
        response = MagicMock()

        gtoken.is_valid = valid_gtoken
        bullet_token.is_valid = valid_bullet

        with (
            patch(regen_path + ".generate_gtoken") as mock_gtoken,
            patch(regen_path + ".generate_bullet_token") as mock_bullet,
            patch(base_regen_path + ".requests") as mock_requests,
            patch(base_regen_path + ".queries") as mock_queries,
            patch(regen_path + ".generate_all_tokens") as mock_all_tokens,
        ):
            mock_gtoken.return_value = gtoken
            mock_bullet.return_value = bullet_token
            mock_requests.post.return_value = response

            if valid_response:
                response.status_code = 200
            else:
                response.status_code = 500

            TokenRegenerator.validate_tokens(
                gtoken,
                bullet_token,
                nso,
                self.ftokens_url,
                "test_user_agent",
            )
            if valid_gtoken:
                mock_gtoken.assert_not_called()
            else:
                mock_gtoken.assert_called_once_with(nso, self.ftokens_url)

            if valid_bullet:
                mock_bullet.assert_not_called()
            else:
                mock_bullet.assert_called_once_with(
                    nso, self.ftokens_url, "test_user_agent"
                )

            mock_queries.query_header.assert_called_once_with(
                bullet_token.value, "en-US", "test_user_agent"
            )
            mock_queries.query_body.assert_called_once_with("HomeQuery")
            mock_requests.post.assert_called_once_with(
                GRAPH_QL_REFERENCE_URL,
                data=mock_queries.query_body.return_value,
                headers=mock_queries.query_header.return_value,
                cookies={"_gtoken": gtoken.value},
            )
            if valid_response:
                mock_all_tokens.assert_not_called()
            else:
                mock_all_tokens.assert_called_once_with(
                    nso, self.ftokens_url, "test_user_agent"
                )
