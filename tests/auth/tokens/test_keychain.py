import time

import freezegun
import pytest

from splatnet3_scraper.auth.tokens.keychain import TokenKeychain
from splatnet3_scraper.auth.tokens.tokens import Token

test_date_str = "2023-01-01 00:00:00"
with freezegun.freeze_time(test_date_str):
    test_date_float = time.time()


class TestTokenKeychain:

    token = Token("test_value", "test_name", test_date_float)

    def test_init(self) -> None:
        keychain = TokenKeychain()
        assert keychain.keychain == {}

    def test_from_dict(self) -> None:
        keychain = TokenKeychain.from_dict({self.token.name: self.token})
        assert keychain.keychain == {self.token.name: self.token}

    def test_from_list(self) -> None:
        keychain = TokenKeychain.from_list([self.token])
        assert keychain.keychain == {self.token.name: self.token}

    def test_get(self) -> None:
        keychain = TokenKeychain.from_list([self.token])
        assert keychain.get(self.token.name) == self.token.value
        with pytest.raises(ValueError):
            keychain.get("invalid")

        assert keychain.get(self.token.name, full_token=True) == self.token

    def test_generate_token(self) -> None:
        keychain = TokenKeychain()
        with freezegun.freeze_time(test_date_str) as frozen_time:
            frozen_time.tick(60)
            new_token = keychain.generate_token(
                self.token.name, self.token.value
            )
            assert new_token.value == self.token.value
            assert new_token.name == self.token.name
            assert new_token.timestamp == test_date_float + 60

    @pytest.mark.parametrize(
        "value",
        [Token("test_value", "test_name", test_date_float), "test_value"],
        ids=["full_token", "from_values"],
    )
    @pytest.mark.parametrize(
        "token_name",
        ["test_name", None],
        ids=["token_name", "no_token_name"],
    )
    @pytest.mark.parametrize(
        "timestamp",
        [test_date_float, None],
        ids=["timestamp", "no_timestamp"],
    )
    def test_add_token(
        self,
        value: str | Token,
        token_name: str | None,
        timestamp: float | None,
    ) -> None:
        keychain = TokenKeychain()
        if isinstance(value, str) and token_name is None:
            with pytest.raises(ValueError):
                keychain.add_token(value, token_name, timestamp)
            return

        with freezegun.freeze_time(test_date_str):
            new_token = keychain.add_token(value, token_name, timestamp)
            assert new_token.value == self.token.value
            assert new_token.name == self.token.name
            if timestamp is None:
                assert new_token.timestamp == test_date_float
            else:
                assert new_token.timestamp == timestamp
            assert keychain.get(self.token.name) == self.token.value
