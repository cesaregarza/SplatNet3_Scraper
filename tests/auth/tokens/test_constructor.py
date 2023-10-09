from unittest.mock import MagicMock, patch

import pytest

from splatnet3_scraper.auth.tokens.constructor import TokenManagerConstructor
from splatnet3_scraper.auth.tokens.manager import TokenManager

base_constructor_path = "splatnet3_scraper.auth.tokens.constructor"


class TestConstructor:
    @pytest.mark.parametrize(
        "with_nso",
        [True, False],
        ids=["with_nso", "without_nso"],
    )
    def test_from_session_token(self, with_nso: bool) -> None:
        nso = MagicMock()
        session_token = MagicMock()
        f_token_url = MagicMock()
        with (
            patch(base_constructor_path + ".NSO") as mock_nso,
            patch(base_constructor_path + ".TokenManager") as mock_manager,
        ):
            mock_nso.new_instance.return_value = nso
            manager = TokenManagerConstructor.from_session_token(
                session_token,
                nso=nso if with_nso else None,
                f_token_url=f_token_url,
            )
            if with_nso:
                mock_nso.new_instance.assert_not_called()
            else:
                mock_nso.new_instance.assert_called_once_with()

            mock_manager.assert_called_once_with(
                nso=nso,
                f_token_url=f_token_url,
                origin="memory",
            )
            mock_manager.return_value.add_token.assert_called_once_with(
                session_token,
                "session_token",
            )
            assert manager == mock_manager.return_value
