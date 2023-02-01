from unittest.mock import patch

import pytest
import pytest_mock

from splatnet3_scraper.scraper.json_parser import JSONParser, LinearJSON
from tests.mock import MockConfig, MockResponse, MockTokenManager

# Paths
json_path = "splatnet3_scraper.scraper.json_parser"
linear_json_path = json_path + ".LinearJSON"
json_parser_path = json_path + ".JSONParser"
linear_json_mangled = linear_json_path + "._LinearJSON"
json_parser_mangled = json_parser_path + "._JSONParser"


class TestLinearJSON:
    def test_init(self):
        header = ["test_header"]
        data = ["test_data"]
        nested_data = [["test_nested_data"]]
        with patch(linear_json_mangled + "__validate") as mock_validate:
            linear_json = LinearJSON(header, data)
            assert linear_json.data == [data]
            assert linear_json.header == header
            mock_validate.assert_called_once()

        with patch(linear_json_mangled + "__validate") as mock_validate:
            linear_json = LinearJSON(header, nested_data)
            assert linear_json.data == nested_data
            assert linear_json.header == header
            mock_validate.assert_called_once()

    def test_from_json(self):
        test_object = {"test_key": "test_value"}
        return_values = ("test_header", "test_data")
        with (
            patch(linear_json_path + ".__init__") as mock_init,
            patch(json_path + ".linearize_json") as mock_linearize,
        ):
            mock_init.return_value = None
            mock_linearize.return_value = return_values
            LinearJSON.from_json(test_object)
            mock_init.assert_called_once_with(
                return_values[0], [return_values[1]]
            )
            mock_linearize.assert_called_once_with(test_object)
