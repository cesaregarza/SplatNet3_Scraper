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

    def test_standardize_new_header(self):

        # Duplicates in header
        header = ["test_header_0", "test_header_1", "test_header_0"]
        data = ["test_data_0", "test_data_1", "test_data_2"]
        linear_json = LinearJSON(header, data)
        with pytest.raises(ValueError):
            linear_json._LinearJSON__standardize_new_header(header)

        def generate_data(header_length):
            header = random.sample(range(header_length * 2), header_length)
            data = list(range(header_length))
            return header, data

        header_length = random.randint(10, 50)
        original_header, data = generate_data(header_length)
        linear_json = LinearJSON(original_header, data)

        # Remove some headers
        new_header_length = header_length // 2
        remove_indices = random.sample(range(header_length), new_header_length)
        remove_indices.sort()
        new_header = [
            original_header[i]
            for i in range(header_length)
            if i not in remove_indices
        ]
        expected_data = [
            data[i] for i in range(header_length) if i not in remove_indices
        ]
        linear_json._LinearJSON__standardize_new_header(new_header)
        assert linear_json.header == new_header
        assert linear_json.data == [expected_data]

        # Add some headers
        original_header, data = generate_data(header_length)
        original_header_copy = original_header.copy()
        data_copy = data.copy()
        new_header_length = header_length + header_length // 2
        insert_indices = random.sample(
            range(new_header_length), new_header_length - header_length
        )
        new_header = [
            original_header_copy.pop(0) if i not in insert_indices else i + 100
            for i in range(new_header_length)
        ]
        expected_data = [
            data_copy.pop(0) if i not in insert_indices else None
            for i in range(new_header_length)
        ]
        linear_json = LinearJSON(original_header, data)
        linear_json._LinearJSON__standardize_new_header(new_header)
        assert linear_json.header == new_header
        assert linear_json.data == [expected_data]

    def test_merge_headers(self):
        header_0 = ["th0", "test_h1", "test_header_2", "test_header_333"]
        header_1 = ["th00", "test_h10", "test_header_2", "test_header_334"]
        expected_header = [
            "th0",
            "th00",
            "test_h1",
            "test_h10",
            "test_header_2",
            "test_header_333",
            "test_header_334",
        ]
        linear_json_0 = LinearJSON(header_0, ["test_data_0"] * len(header_0))
        linear_json_1 = LinearJSON(header_1, ["test_data_1"] * len(header_1))
        new_header = LinearJSON.merge_headers(linear_json_0, linear_json_1)
        assert new_header == expected_header

    def test_append(self):
        header = ["test_header_0", "test_header_1"]
        alt_header = ["test_header_0", "test_header_2", "test_header_3"]
        data = ["test_data_0", "test_data_1"]
        alt_data = ["test_data_0", "test_data_2", "test_data_3"]
        linear_json = LinearJSON(header, data)
        alt_linear_json = LinearJSON(alt_header, alt_data)
        linear_json.append(alt_linear_json)
        expected_header = [
            "test_header_0",
            "test_header_1",
            "test_header_2",
            "test_header_3",
        ]
        expected_data = [
            ["test_data_0", "test_data_1", None, None],
            ["test_data_0", None, "test_data_2", "test_data_3"],
        ]
        assert linear_json.header == expected_header
        assert linear_json.data == expected_data

    def test_transpose(self):
        header = ["test_header_0", "test_header_1"]
        data = [
            ["test_data_0", "test_data_1"],
            ["test_data_2", "test_data_3"],
            ["test_data_4", "test_data_5"],
        ]
        linear_json = LinearJSON(header, data)
        transposed_data = linear_json.transpose()
        expected_data = [
            ["test_data_0", "test_data_2", "test_data_4"],
            ["test_data_1", "test_data_3", "test_data_5"],
        ]
        assert transposed_data == expected_data

    def test_stringify(self):
        # No special characters
        header = ["test_header_0", "test_header_1"]
        data = [
            ["test_data_0", "test_data_1"],
            ["test_data_2", "test_data_3"],
            ["test_data_4", "test_data_5"],
        ]
        linear_json = LinearJSON(header, data)
        expected_header = "test_header_0,test_header_1"
        expected_string = (
            "test_data_0,test_data_1\n"
            "test_data_2,test_data_3\n"
            "test_data_4,test_data_5"
        )
        assert linear_json.stringify() == (expected_header, expected_string)
        assert linear_json.stringify(include_header=False) == expected_string

        # Commas in data
        header = ["test_header_0", "test_header_1"]
        data = [
            ["test_data_0", "test_data_1"],
            ["test_data_2", "test_data_3,3"],
            ["test_data_4", "test_data_5"],
        ]
        linear_json = LinearJSON(header, data)
        expected_header = "test_header_0,test_header_1"
        expected_string = (
            "test_data_0,test_data_1\n"
            'test_data_2,"test_data_3,3"\n'
            "test_data_4,test_data_5"
        )
        assert linear_json.stringify() == (expected_header, expected_string)
        assert linear_json.stringify(include_header=False) == expected_string

    def test_remove_columns(self):
        header = ["test_header_0", "test_header_1", "test_header_2"]
        data = [["test_data_0", "test_data_1", "test_data_2"]]
        linear_json = LinearJSON(header, data)
        with patch(linear_json_mangled + "__standardize_new_header") as mock:
            linear_json.remove_columns(["test_header_0", "test_header_2"])
            mock.assert_called_once_with(["test_header_1"])

    def test_remove_url_columns(self):
        header = ["test_header_0URL", "test_header_1", "test_header_2url"]
        data = [["test_data_0", "test_data_1", "test_data_2"]]
        linear_json = LinearJSON(header, data)
        with patch(linear_json_mangled + "__standardize_new_header") as mock:
            linear_json.remove_url_columns()
            mock.assert_called_once_with(["test_header_1"])


class TestJSONParser:
    def test_init(self):
        data = {"test_key": "test_value"}
        assert JSONParser(data).data == [data]
        assert JSONParser([data]).data == [data]
