from unittest.mock import patch

import pytest

from splatnet3_scraper.auth.environment_manager import (
    EnvironmentVariablesManager,
)
from splatnet3_scraper.constants import ENV_VAR_NAMES, TOKENS


class TestEnvironmentVariablesManager:
    def test_init(self):
        manager = EnvironmentVariablesManager()
        assert manager.variable_names == {
            TOKENS.SESSION_TOKEN: ENV_VAR_NAMES[TOKENS.SESSION_TOKEN],
            TOKENS.GTOKEN: ENV_VAR_NAMES[TOKENS.GTOKEN],
            TOKENS.BULLET_TOKEN: ENV_VAR_NAMES[TOKENS.BULLET_TOKEN],
        }

    def test_token_to_variable(self):
        manager = EnvironmentVariablesManager()
        assert (
            manager.token_to_variable(TOKENS.SESSION_TOKEN)
            == ENV_VAR_NAMES[TOKENS.SESSION_TOKEN]
        )
        assert (
            manager.token_to_variable(TOKENS.GTOKEN)
            == ENV_VAR_NAMES[TOKENS.GTOKEN]
        )
        assert (
            manager.token_to_variable(TOKENS.BULLET_TOKEN)
            == ENV_VAR_NAMES[TOKENS.BULLET_TOKEN]
        )

    def test_variable_to_token(self):
        manager = EnvironmentVariablesManager()
        assert (
            manager.variable_to_token(ENV_VAR_NAMES[TOKENS.SESSION_TOKEN])
            == TOKENS.SESSION_TOKEN
        )
        assert (
            manager.variable_to_token(ENV_VAR_NAMES[TOKENS.GTOKEN])
            == TOKENS.GTOKEN
        )
        assert (
            manager.variable_to_token(ENV_VAR_NAMES[TOKENS.BULLET_TOKEN])
            == TOKENS.BULLET_TOKEN
        )
        with pytest.raises(KeyError):
            manager.variable_to_token("test_variable")

    def test_add_token(self):
        manager = EnvironmentVariablesManager()
        assert "test_token" not in manager.variable_names
        manager.add_token("test_token", "test_variable")
        assert manager.variable_names["test_token"] == "test_variable"

    def test_remove_token(self):
        manager = EnvironmentVariablesManager()
        assert TOKENS.SESSION_TOKEN in manager.variable_names
        for token in manager.BASE_TOKENS:
            with pytest.raises(ValueError):
                manager.remove_token(token)

        manager.add_token("test_token", "test_variable")
        assert "test_token" in manager.variable_names
        manager.remove_token("test_token")
        assert "test_token" not in manager.variable_names

    def test_get(self, monkeypatch: pytest.MonkeyPatch):
        manager = EnvironmentVariablesManager()
        with monkeypatch.context() as ctx:
            test_token = "test_session_token"
            ctx.setenv(ENV_VAR_NAMES[TOKENS.SESSION_TOKEN], test_token)
            assert manager.get(TOKENS.SESSION_TOKEN) == test_token
            assert manager.get(TOKENS.GTOKEN) is None

    @pytest.mark.parametrize(
        "session_token",
        [None, "test_session_token"],
        ids=["no_session_token", "session_token"],
    )
    @pytest.mark.parametrize(
        "gtoken",
        [None, "test_gtoken"],
        ids=["no_gtoken", "gtoken"],
    )
    @pytest.mark.parametrize(
        "bullet_token",
        [None, "test_bullet_token"],
        ids=["no_bullet_token", "bullet_token"],
    )
    @pytest.mark.parametrize(
        "extra_token",
        [None, "test_extra_token"],
        ids=["no_extra_token", "extra_token"],
    )
    def test_get_all(
        self,
        session_token: str,
        gtoken: str,
        bullet_token: str,
        extra_token: str,
        monkeypatch: pytest.MonkeyPatch,
    ):
        manager = EnvironmentVariablesManager()
        if extra_token is not None:
            manager.add_token("test_token", "test_variable")

        with monkeypatch.context() as ctx:
            if session_token is not None:
                ctx.setenv(ENV_VAR_NAMES[TOKENS.SESSION_TOKEN], session_token)
            if gtoken is not None:
                ctx.setenv(ENV_VAR_NAMES[TOKENS.GTOKEN], gtoken)
            if bullet_token is not None:
                ctx.setenv(ENV_VAR_NAMES[TOKENS.BULLET_TOKEN], bullet_token)
            if extra_token is not None:
                ctx.setenv("test_variable", extra_token)

            tokens = manager.get_all()
            assert isinstance(tokens, dict)
            assert tokens[TOKENS.SESSION_TOKEN] == session_token
            assert tokens[TOKENS.GTOKEN] == gtoken
            assert tokens[TOKENS.BULLET_TOKEN] == bullet_token
            if extra_token is not None:
                assert tokens["test_token"] == extra_token
