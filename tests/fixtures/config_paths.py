import pathlib

import pytest

config_path = pathlib.Path(__file__).parent / "config_files"


@pytest.fixture
def extra_tokens() -> str:
    return str(config_path / ".extra_tokens")


@pytest.fixture
def no_data() -> str:
    return str(config_path / ".no_data")


@pytest.fixture
def no_tokens_section() -> str:
    return str(config_path / ".no_tokens_section")


@pytest.fixture
def valid() -> str:
    return str(config_path / ".valid")


@pytest.fixture
def valid_with_ftoken() -> str:
    return str(config_path / ".valid_with_ftoken")


@pytest.fixture
def valid_with_ftoken_list() -> str:
    return str(config_path / ".valid_with_ftoken_list")
