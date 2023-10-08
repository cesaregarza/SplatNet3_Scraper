import pathlib
import time
from typing import Literal
from unittest.mock import MagicMock, mock_open, patch

import freezegun
import pytest
import pytest_mock
import requests

from splatnet3_scraper.auth.tokens.manager import ManagerOrigin, TokenManager
from splatnet3_scraper.constants import IMINK_URL, TOKENS

ftoken_urls = [
    "ftoken_url_1",
    "ftoken_url_2",
    "ftoken_url_3",
    "ftoken_url_4",
]

base_token_manager_path = "splatnet3_scraper.auth.tokens.manager"
token_manager_path = base_token_manager_path + ".TokenManager"


class TestTokenManager:
    @pytest.mark.parametrize(
        "with_nso",
        [True, False],
        ids=["with_nso", "without_nso"],
    )
    @pytest.mark.parametrize(
        "f_token_url",
        [
            ftoken_urls[0],
            ftoken_urls,
            None,
        ],
        ids=["single_url", "multiple_urls", "default_url"],
    )
    @pytest.mark.parametrize(
        "with_env_manager",
        [True, False],
        ids=["with_env_manager", "without_env_manager"],
    )
    @pytest.mark.parametrize(
        "with_origin",
        [True, False],
        ids=["with_origin", "without_origin"],
    )
    @pytest.mark.parametrize(
        "with_origin_data",
        [True, False],
        ids=["with_origin_data", "without_origin_data"],
    )
    def test_init(
        self,
        with_nso: bool,
        f_token_url: str | list[str] | None,
        with_env_manager: bool,
        with_origin: bool,
        with_origin_data: bool,
    ) -> None:
        nso = MagicMock()
        env_manager = MagicMock()

        with (
            patch(base_token_manager_path + ".NSO") as mock_nso,
            patch(
                base_token_manager_path + ".EnvironmentVariablesManager"
            ) as mock_env_manager,
            patch(base_token_manager_path + ".TokenKeychain") as mock_keychain,
            patch(base_token_manager_path + ".ManagerOrigin") as mock_origin,
        ):
            mock_nso.new_instance.return_value = nso
            mock_env_manager.return_value = env_manager

            instance = TokenManager(
                nso=nso if with_nso else None,
                f_token_url=f_token_url,
                env_manager=env_manager if with_env_manager else None,
                origin="origin" if with_origin else "memory",
                origin_data="test_data" if with_origin_data else None,
            )

            if with_nso:
                mock_nso.new_instance.assert_not_called()
            else:
                mock_nso.new_instance.assert_called_once()

            if with_env_manager:
                mock_env_manager.assert_not_called()
            else:
                mock_env_manager.assert_called_once()

            if isinstance(f_token_url, str):
                expected_f_token_url = [f_token_url]
            elif f_token_url is None:
                expected_f_token_url = [IMINK_URL]
            else:
                expected_f_token_url = f_token_url

            assert instance.nso == nso
            assert instance.f_token_url == expected_f_token_url
            assert instance.env_manager == env_manager
            assert instance.keychain == mock_keychain.return_value
            assert instance.origin == mock_origin.return_value

            mock_origin.assert_called_once_with(
                "origin" if with_origin else "memory",
                "test_data" if with_origin_data else None,
            )
