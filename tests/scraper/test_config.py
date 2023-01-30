import configparser
import unittest
from unittest.mock import mock_open, patch

import pytest
import pytest_mock

from splatnet3_scraper.scraper.config import Config


class TestConfig:
    def test_init(self, mocker: pytest_mock.MockFixture):
        mock_post_init = mocker.patch.object(Config, "__post_init__")
        config = Config()
        mock_post_init.assert_called_once_with(None)
