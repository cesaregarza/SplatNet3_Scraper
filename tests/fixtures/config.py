import configparser
import pathlib
import tempfile

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


@pytest.fixture
def all_path() -> str:
    return str(config_path / ".all")


@pytest.fixture
def expected_all() -> str:
    return str(config_path / ".expected_all")


@pytest.fixture
def s3s_config() -> str:
    return str(config_path / "s3sconfig.txt")


@pytest.fixture
def all_config(all_path) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(all_path)
    return config


@pytest.fixture
def temp_file() -> str:
    with tempfile.NamedTemporaryFile() as f:
        yield f.name
