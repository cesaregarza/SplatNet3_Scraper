import pathlib
import random
from unittest.mock import mock_open, patch

import pyarrow as pa
import pytest
import pytest_mock

from splatnet3_scraper.scraper.json_parser import JSONParser, LinearJSON
from tests.mock import MockLinearJSON, MockPyArrowTable

# Paths
json_path = "splatnet3_scraper.scraper.json_parser"
mock_path = "tests.mock"
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
            assert isinstance(delinearized, dict)
            assert isinstance(delinearized["data"], list)

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

    def test_len(self):
        length = random.randint(1, 100)
        data = [{"test_key": "test_value"}] * length
        assert len(JSONParser(data)) == length

    def test_eq(self):
        data_0 = {"test_key_0": "test_value_0"}
        data_1 = {"test_key_1": "test_value_1"}
        assert JSONParser(data_0) == JSONParser(data_0)
        assert JSONParser(data_0) != JSONParser(data_1)
        assert JSONParser(data_0) != "test"

    def test_repr(self):
        length = random.randint(1, 100)
        data = [{"test_key": "test_value"}] * length
        assert repr(JSONParser(data)) == f"JSONParser({length} battles)"

    def test_to_linear_json(self):
        data = [{"test_key": "test_value_0"}, {"test_key": "test_value_1"}]
        linear_json = JSONParser(data)._JSONParser__to_linear_json()
        assert linear_json.header == ("test_key",)
        assert linear_json.data == [["test_value_0"], ["test_value_1"]]

    def test_remove_columns(self):
        data = [
            {"test_key_0": "test_value_0", "test_key_1": "test_value_1"},
            {"test_key_0": "test_value_2", "test_key_1": "test_value_3"},
        ]
        json_parser = JSONParser(data)
        remove_columns = ["test_key_0"]
        expected_data = [
            {"test_key_1": "test_value_1"},
            {"test_key_1": "test_value_3"},
        ]
        json_parser.remove_columns(remove_columns)
        assert json_parser.data == expected_data

    def test_remove_url_columns(self):
        data = [
            {"test_key_0URL": "test_value_0", "test_key_1": "test_value_1"},
            {"test_key_0url": "test_value_2", "test_key_1": "test_value_3"},
        ]
        json_parser = JSONParser(data)
        expected_data = [
            {"test_key_1": "test_value_1"},
            {"test_key_1": "test_value_3"},
        ]
        json_parser.remove_url_columns()
        assert json_parser.data == expected_data

    def test_to_csv(self):
        data = [
            {"test_key_0": "test_value_0", "test_key_1": "test_value_1"},
            {"test_key_0": "test_value_2", "test_key_1": "test_value_3"},
        ]
        json_parser = JSONParser(data)
        expected_header = "test_key_0,test_key_1"
        expected_string = (
            "test_value_0,test_value_1\n" "test_value_2,test_value_3"
        )
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch(json_parser_mangled + "__to_linear_json") as mock_linear_json,
            patch(mock_path + ".MockLinearJSON.stringify") as mock_stringify,
        ):
            mock_linear_json.return_value = MockLinearJSON()
            mock_stringify.return_value = (expected_header, expected_string)
            json_parser.to_csv("test_path")
            mock_file.assert_called_once_with(
                "test_path", "w", encoding="utf-8"
            )
            mock_linear_json.assert_called_once()
            mock_stringify.assert_called_once()
            mock_file().write.call_count == 2

    def test_to_json(self):
        data = [
            {"test_key_0": "test_value_0", "test_key_1": "test_value_1"},
            {"test_key_0": "test_value_2", "test_key_1": "test_value_3"},
        ]
        json_parser = JSONParser(data)

        # No given kwargs
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("json.dump") as mock_dump,
        ):
            json_parser.to_json("test_path")
            mock_file.assert_called_once_with(
                "test_path", mode="w", encoding="utf-8"
            )
            mock_dump.assert_called_once_with(data, mock_file(), indent=4)

        # With kwargs
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("json.dump") as mock_dump,
        ):
            json_parser.to_json("test_path", indent=2)
            mock_file.assert_called_once_with(
                "test_path", mode="w", encoding="utf-8"
            )
            mock_dump.assert_called_once_with(data, mock_file(), indent=2)

    def test_to_gzipped_json(self):
        data = [
            {"test_key_0": "test_value_0", "test_key_1": "test_value_1"},
            {"test_key_0": "test_value_2", "test_key_1": "test_value_3"},
        ]
        json_parser = JSONParser(data)
        with (
            patch("gzip.open", mock_open()) as mock_file,
            patch("json.dump") as mock_dump,
        ):
            json_parser.to_gzipped_json("test_path")
            mock_file.assert_called_once_with(
                "test_path", mode="wt", encoding="utf-8"
            )
            mock_dump.assert_called_once_with(data, mock_file(), indent=4)

    def test_to_parquet(self, monkeypatch: pytest.MonkeyPatch):
        data = [
            {"test_key_0": "test_value_0", "test_key_1": "test_value_1"},
            {"test_key_0": "test_value_2", "test_key_1": "test_value_3"},
        ]
        json_parser = JSONParser(data)
        with (
            patch("pyarrow.array") as mock_pa_array,
            patch("pyarrow.parquet.write_table") as mock_write,
            monkeypatch.context() as m,
        ):
            pa_return = ["test_value_0", "test_value_1"]
            mock_pa_array.return_value = pa_return
            # PyArrow Table is immutable so we mock the full class instead of
            # any of the methods
            m.setattr(pa, "Table", MockPyArrowTable)
            json_parser.to_parquet("test_path")
            mock_pa_array.call_count == 2
            array_call_args = mock_pa_array.call_args_list
            assert array_call_args[0][0][0][0] == "test_value_0"
            assert array_call_args[0][0][0][1] == "test_value_2"
            assert array_call_args[1][0][0][0] == "test_value_1"
            assert array_call_args[1][0][0][1] == "test_value_3"
            write_call_args = mock_write.call_args_list[0][0]
            assert isinstance(write_call_args[0], MockPyArrowTable)
            assert write_call_args[1] == "test_path"

    def test_from_csv(self, json_with_none):

        # No commas
        base_path = pathlib.Path(__file__).parent.parent / "fixtures"
        no_comma_path = str(base_path / "linear_json.csv")
        json_parser = JSONParser.from_csv(no_comma_path)
        assert json_parser.data == [json_with_none]

        # With commas
        comma_path = str(base_path / "linear_json_with_commas.csv")
        json_parser = JSONParser.from_csv(comma_path)
        expected_json = {
            "a": 1,
            "b,": 2,
            "c": [
                None,
                {
                    "d,": 3,
                    "e": 4,
                },
            ],
        }
        assert json_parser.data == [expected_json]

    def test_automatic_type_conversion(self):
        test_values = [
            "",
            "1",
            "1.0",
            "true",
            "false",
            "null",
            "[]",
            "{}",
            "['a', 'b']",
        ]
        expected_values = [None, 1, 1.0, True, False, None, [], {}, ["a", "b"]]
        JSONParser.automatic_type_conversion(test_values) == expected_values

    def test_from_json(self):
        data = [
            {"test_key_0": "test_value_0", "test_key_1": "test_value_1"},
            {"test_key_0": "test_value_2", "test_key_1": "test_value_3"},
        ]
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("json.load") as mock_load,
        ):
            mock_load.return_value = data
            json_parser = JSONParser.from_json("test_path")
            mock_file.assert_called_once_with(
                "test_path", "r", encoding="utf-8"
            )
            mock_load.assert_called_once()
            assert json_parser.data == data

    def test_from_gzipped_json(self):
        data = [
            {"test_key_0": "test_value_0", "test_key_1": "test_value_1"},
            {"test_key_0": "test_value_2", "test_key_1": "test_value_3"},
        ]
        with (
            patch("gzip.open", mock_open()) as mock_file,
            patch("json.load") as mock_load,
        ):
            mock_load.return_value = data
            json_parser = JSONParser.from_gzipped_json("test_path")
            mock_file.assert_called_once_with(
                "test_path", "rt", encoding="utf-8"
            )
            mock_load.assert_called_once()
            assert json_parser.data == data
