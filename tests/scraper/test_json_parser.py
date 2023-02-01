import random
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

    def test_delinearize(self):
        x_length = random.randint(10, 50)
        y_length = random.randint(5, 10)
        header = [f"test_header_{i}" for i in range(x_length)]
        data = [
            [f"test_data_{j}_{i}" for i in range(x_length)]
            for j in range(y_length)
        ]
        linear_json = LinearJSON(header, data)
        with patch(json_path + ".delinearize_json") as mock_delinearize:
            mock_delinearize.return_value = None
            delinearized = linear_json.delinearize()
            assert mock_delinearize.call_count == y_length
            assert list(delinearized.keys()) == ["data"]
            assert len(delinearized["data"]) == y_length

    def test_eq(self):
        header = ["test_header_0", "test_header_1"]
        data = ["test_data_0", "test_data_1"]
        linear_json = LinearJSON(header, data)
        assert linear_json == LinearJSON(header, data)
        assert linear_json != LinearJSON(header, data[::-1])
        assert linear_json != LinearJSON(["test_header_2"], data[:1])
        assert linear_json != LinearJSON(["test_header_2"], ["test_data_2"])
        assert linear_json != "test"
        assert linear_json == [header, data]

    def test__validate(self):
        # Valid
        LinearJSON(["test_header"], ["test_data"])
        LinearJSON(["test_header"], [["test_data_0"], ["test_data_1"]])

        # Invalid: not all data is the same length
        with pytest.raises(ValueError):
            LinearJSON(
                ["test_header"],
                [["test_data_0"], ["test_data_1", "test_data_2"]],
            )
