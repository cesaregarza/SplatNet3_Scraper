from unittest.mock import MagicMock, patch

import pytest

from splatnet3_scraper.auth.tokens.constructor import TokenManagerConstructor

base_constructor_path = "splatnet3_scraper.auth.tokens.constructor"
constructor_path = base_constructor_path + ".TokenManagerConstructor"


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

    @pytest.mark.parametrize(
        "with_gtoken",
        [True, False],
        ids=["with_gtoken", "without_gtoken"],
    )
    @pytest.mark.parametrize(
        "with_bullet_token",
        [True, False],
        ids=["with_bullet_token", "without_bullet_token"],
    )
    def test_from_tokens(
        self, with_gtoken: bool, with_bullet_token: bool
    ) -> None:
        nso = MagicMock()
        session_token = MagicMock()
        gtoken = MagicMock()
        bullet_token = MagicMock()
        f_token_url = MagicMock()
        user_agent = MagicMock()

        with (
            patch(base_constructor_path + ".NSO") as mock_nso,
            patch(
                base_constructor_path + ".TokenRegenerator"
            ) as mock_regenerator,
            patch(
                constructor_path + ".from_session_token"
            ) as mock_from_session_token,
        ):
            mock_regenerator.generate_gtoken.return_value.value = gtoken
            mock_regenerator.generate_bullet_token.return_value.value = (
                bullet_token
            )
            mock_from_session_token.return_value.nso = nso
            mock_from_session_token.return_value.f_token_url = f_token_url
            manager = TokenManagerConstructor.from_tokens(
                session_token,
                gtoken=gtoken if with_gtoken else None,
                bullet_token=bullet_token if with_bullet_token else None,
                nso=nso,
                f_token_url=f_token_url,
                user_agent=user_agent,
            )
            mock_from_session_token.assert_called_once_with(
                session_token,
                nso=nso,
                f_token_url=f_token_url,
            )
            if with_gtoken:
                mock_regenerator.generate_gtoken.assert_not_called()

            else:
                mock_regenerator.generate_gtoken.assert_called_once_with(
                    nso, f_token_url
                )
            manager.add_token.assert_any_call(gtoken, "gtoken")

            if with_bullet_token:
                mock_regenerator.generate_bullet_token.assert_not_called()
            else:
                mock_regenerator.generate_bullet_token.assert_called_once_with(
                    nso, f_token_url, user_agent=user_agent
                )
            manager.add_token.assert_any_call(bullet_token, "bullet_token")

            assert manager == mock_from_session_token.return_value

    @pytest.mark.parametrize(
        "with_env_manager",
        [True, False],
        ids=["with_env_manager", "without_env_manager"],
    )
    def test_from_env(
        self,
        with_env_manager: bool,
    ) -> None:
        nso = MagicMock()
        f_token_url = MagicMock()
        user_agent = MagicMock()
        env_manager = MagicMock()

        with (
            patch(constructor_path + ".from_tokens") as mock_from_tokens,
            patch(
                base_constructor_path + ".EnvironmentVariablesManager"
            ) as mock_env_manager,
        ):
            mock_env_manager.return_value = env_manager
            manager = TokenManagerConstructor.from_env(
                nso=nso,
                f_token_url=f_token_url,
                user_agent=user_agent,
                env_manager=env_manager if with_env_manager else None,
            )
            if with_env_manager:
                mock_env_manager.assert_not_called()
            else:
                mock_env_manager.assert_called_once_with()

            env_manager.get_all.assert_called_once_with()
            env_get_all: MagicMock = env_manager.get_all.return_value
            session_token = env_get_all.__getitem__.return_value
            env_get_all.get.assert_any_call("gtoken", None)
            env_get_all.get.assert_any_call("bullet_token", None)
            mock_from_tokens.assert_called_once_with(
                session_token=session_token,
                gtoken=env_get_all.get.return_value,
                bullet_token=env_get_all.get.return_value,
                nso=nso,
                f_token_url=f_token_url,
                user_agent=user_agent,
            )
            mock_from_tokens.return_value.flag_origin.assert_called_once_with(
                "env"
            )
            assert manager == mock_from_tokens.return_value
