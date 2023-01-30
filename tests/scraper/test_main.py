from unittest.mock import mock_open, patch
import requests

import pytest
import pytest_mock

from splatnet3_scraper.scraper.main import SplatNet3_Scraper
from tests.mock import MockResponse, MockConfig

