import ast
import csv
import gzip
import hashlib
import json
from typing import Any, Callable, Literal, overload

from splatnet3_scraper.utils import delinearize_json, linearize_json


class LinearJSON:
    """Class containing methods for linearized JSON objects."""

    def __init__(
        self, header: list[str] | tuple[str, ...], data: list[list] | list
    ) -> None:
        """Initializes a LinearJSON.

        Args:
            header (list[str]): The header of the JSON object.
            data (list[Any]): The data of the JSON object.
        """
        self.header = header
        self.data = data if isinstance(data[0], list) else [data]
        self.__validate()

    @staticmethod
    def from_json(object: dict[str, Any]) -> "LinearJSON":
        """Creates a LinearJSON object from a JSON object.

        Args:
            object (dict[str, Any]): The JSON object to convert.

        Returns:
            LinearJSON: The LinearJSON object.
        """
        header, data = linearize_json(object)
        return LinearJSON(header, [data])

    @staticmethod
    def hash(obj: list[str] | tuple[str, ...]) -> str:
        """Returns the hash of the header.

        Args:
            obj (list[str] | tuple[str, ...]): The header to hash.

        Returns:
            str: The hash of the header.
        """
        header_tuple = tuple(obj)
        # Use a stable hash function to ensure the same hash is generated
        # across different Python versions
        return hashlib.sha256(str(header_tuple).encode()).hexdigest()

    def hashed_header(self) -> str:
        """Returns the hash of the header.

        Returns:
            str: The hash of the header.
        """
        return self.hash(self.header)

    def delinearize(self) -> dict[str, list[dict[str, Any]]]:
        """Delinearizes the JSON object into a big JSON object.

        Returns:
            dict[str, list[dict[str, Any]]]: The big JSON object.
        """
        out: dict[str, list[dict[str, Any]]] = {"data": []}
        for row in self.data:
            out["data"].append(delinearize_json(self.header, row))
        return out

    def __eq__(self, other: object) -> bool:
        """Returns whether the other object is equal to this object.

        Args:
            other (object): The other object to compare.

        Returns:
            bool: Whether the other object is equal to this object.
        """
        if isinstance(other, LinearJSON):
            return self.header == other.header and self.data == other.data
        elif isinstance(other, list):
            return self.header == other[0] and self.data == other[1:]
        return False

    def __validate(self) -> None:
        """Validates the header and data of the LinearJSON object.

        Raises:
            ValueError: If the header and data are not the same length.
        """
        for row in self.data:
            try:
                assert len(row) == len(self.header)
            except AssertionError:
                raise ValueError("The header and data are not the same length.")

    def __standardize_new_header(self, new_header: list[str]) -> None:
        """If the new header is different from the current header, this method
        will remove columns from the data that are not in the new header and add
        None values for columns that are in the new header but not the current
        header.

        Raises:
            ValueError: If the new header has duplicate columns.

        Args:
            new_header (list[str]): The new header.
        """
        new_header_columns = [x for x in new_header if x not in self.header]
        removed_header_columns = [x for x in self.header if x not in new_header]

        # Check if the new header has any duplicates and raise an error if so
        if len(new_header) != len(set(new_header)):
            raise ValueError("The new header has duplicate columns.")

        if (not new_header_columns) and (not removed_header_columns):
            return
        new_data = []
        for row in self.data:
            new_row: list[Any] = []
            for col in new_header:
                if col in new_header_columns:
                    new_row.append(None)
                elif col in removed_header_columns:
                    # Shouldn't happen, but making the logic explicit
                    continue
                else:
                    original_index = self.header.index(col)
                    new_row.append(row[original_index])

            new_data.append(new_row)
        self.header = new_header
        self.data = new_data

    @staticmethod
    def merge_headers(left: "LinearJSON", right: "LinearJSON") -> list[str]:
        """Merges the headers of the two given LinearJSON objects.

        Args:
            left (LinearJSON): The left LinearJSON object to merge.
            right (LinearJSON): The right LinearJSON object to merge.

        Returns:
            list[str]: The new header.
        """
        new_header_set = set(left.header).union(set(right.header))
        new_header = list(new_header_set)
        new_header = sorted(new_header, key=lambda x: (len(x), x))
        return new_header

    def append(self, other: "LinearJSON") -> None:
        """Appends a LinearJSON object to this one. If the headers are not the
        same, the headers will be merged and the data will be standardized to
        the new header.

        Args:
            other (LinearJSON): The other LinearJSON object to append.
        """
        if self.header != other.header:
            new_header = self.merge_headers(self, other)
            # New header will have new columns anywhere in the header, so we
            # need to identify the new columns and insert None values for them
            # in the data
            obj_list: list[LinearJSON] = [self, other]
            for obj in obj_list:
                obj.__standardize_new_header(new_header)
        self.data.extend(other.data)

    def transpose(self) -> list[list[Any]]:
        """Transposes the data.

        Returns:
            list[list[Any]]: The transposed data.
        """
        return [list(x) for x in zip(*self.data)]

    @overload
    def stringify(self, include_header: Literal[True] = ...) -> tuple[str, str]:
        ...

    @overload
    def stringify(self, include_header: Literal[False]) -> str:
        ...

    @overload
    def stringify(self, include_header: bool) -> str | tuple[str, str]:
        ...

    def stringify(
        self,
        include_header: bool = True,
    ) -> str | tuple[str, str]:
        """Stringifies the LinearJSON object. If include_header is True, then
        the header and data are returned as a tuple. Otherwise, only the data
        is returned as a string.

        Args:
            include_header (bool): Whether to include the header. Defaults to
                True.

        Returns:
            str | tuple[str, str]: The header and data as a string, or just the
                data as a string.
        """
        data = self.data
        data_str = []
        for row in data:
            out_row = []
            # If the row has a comma, then we need to wrap the row in quotes
            for col in row:
                if isinstance(col, str) and "," in col:
                    out_col = f'"{col}"'
                else:
                    out_col = str(col)
                out_row.append(out_col)
            data_str.append(",".join(out_row))
        data_str_out = "\n".join(data_str)
        if include_header:
            header_str = ",".join(self.header)
            return header_str, data_str_out
        return data_str_out

    def remove_columns(self, columns: list[str]) -> None:
        """Removes columns from the LinearJSON object.

        Args:
            columns (list[str]): The columns to remove. If a column is not in
                the header, it will be ignored.
        """
        new_header = [x for x in self.header if x not in columns]
        self.__standardize_new_header(new_header)

    def remove_url_columns(self) -> None:
        """Removes columns that are URLs from the LinearJSON object."""
        url_columns = [x for x in self.header if x.lower().endswith("url")]
        self.remove_columns(url_columns)


class JSONParser:
    """Class containing JSON methods for saving and loading data."""

    def __init__(self, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        """Initializes a JSONParser.

        Args:
            data (dict[str, Any] | list[dict[str, Any]]): The data to parse.
        """
        if isinstance(data, dict):
            data = [data]
        self.data = data

    def __len__(self) -> int:
        return len(self.data)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, JSONParser):
            return self.data == other.data
        return False

    def __repr__(self) -> str:
        return f"JSONParser({len(self)} rows)"

    def __to_linear_json(self) -> LinearJSON:
        """Converts the JSON object to a LinearJSON object.

        Returns:
            LinearJSON: The LinearJSON object.
        """
        header, data = linearize_json(self.data[0])
        out = LinearJSON(header, data)
        for row in self.data[1:]:
            header, data = linearize_json(row)
            out.append(LinearJSON(header, data))
        return out

    def remove_columns(self, columns: list[str]) -> None:
        """Removes columns from the data.

        Args:
            columns (list[str]): The columns to remove.
        """
        linear_json = self.__to_linear_json()
        linear_json.remove_columns(columns)
        self.data = linear_json.delinearize()["data"]

    def remove_url_columns(self) -> None:
        """Removes URL columns from the data."""
        linear_json = self.__to_linear_json()
        linear_json.remove_url_columns()
        self.data = linear_json.delinearize()["data"]

    def to_csv(self, path: str) -> None:
        """Saves the JSON object to a CSV file.

        Given the JSON Parser's data, this method will save the data to a CSV by
        linearizing the JSON object. Given the following example JSON object:

        >>> json = {
        ...     "a": 1,
        ...     "b": {
        ...         "c": 2,
        ...         "d": 3,
        ...     },
        ...     "e": [4, 5, 6],
        ...     "f": [
        ...         {"g": 7, "h": 8},
        ...         {"g": 9, "h": 10},
        ...     ],
        ... }

        The following CSV file will be created with spaces added for clarity:

        >>> "a, b.c, b.d, e;0, e;1, e;2, f;0.g, f;0.h, f;1.g, f;1.h"
        ... "1, 2, 3, 4, 5, 6, 7, 8, 9, 10"

        Args:
            path (str): The path to save the CSV file to.
        """
        linear_json = self.__to_linear_json()
        with open(path, "w", encoding="utf-8") as f:
            header, data = linear_json.stringify()
            f.write(header + "\n")
            f.write(data)

    def __to_json(self, path: str, use_gzip: bool, **kwargs) -> None:
        """Saves the JSON object to a JSON file. Any keyword arguments are
        passed to the json.dump method. If gzip is True, the file will be
        compressed with gzip.

        Args:
            path (str): The path to save the JSON file to.
            use_gzip (bool): Whether or not to compress the file with gzip.
            **kwargs: Any keyword arguments to pass to the json.dump method.
        """
        default_kwargs: dict[str, Any] = {"indent": 4}
        default_kwargs.update(kwargs)
        if use_gzip:
            open_function: Callable = gzip.open
            open_kwargs = {"mode": "wt", "encoding": "utf-8"}
        else:
            open_function = open
            open_kwargs = {"mode": "w", "encoding": "utf-8"}

        with open_function(path, **open_kwargs) as f:
            json.dump(self.data, f, **default_kwargs)

    def to_json(self, path: str, **kwargs) -> None:
        """Saves the JSON object to a JSON file. Any keyword arguments are
        passed to the json.dump method.

        Args:
            path (str): The path to save the JSON file to.
            **kwargs: Keyword arguments to pass to the json.dump method.
        """
        self.__to_json(path, False, **kwargs)

    def to_gzipped_json(self, path: str, **kwargs) -> None:
        """Saves the JSON object to a gzipped JSON file. Any keyword arguments
        are passed to the json.dump method.

        Args:
            path (str): The path to save the gzipped JSON file to.
            **kwargs: Keyword arguments to pass to the json.dump method.
        """
        self.__to_json(path, True, **kwargs)

    def to_parquet(self, path: str, **kwargs) -> None:
        """Saves the JSON object to a Parquet file. Any keyword arguments are
        passed to the pandas.DataFrame.to_parquet method.

        Args:
            path (str): The path to save the Parquet file to.
            **kwargs: Keyword arguments to pass to the pq.write_table method.

        Raises:
            ImportError: If the parquet extra is not installed.
        """
        try:
            import numpy as np
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError(
                "parquet format requires the [parquet] extra to be installed. "
                'Try "pip install splatnet3_scraper[parquet]" or "poetry '
                'install --extras parquet" if you are developing.'
            )
        linear_json = self.__to_linear_json()
        numpy_data = np.array(linear_json.data)
        arrays = [pa.array(data) for data in numpy_data.T]
        del numpy_data
        table = pa.Table.from_arrays(arrays, names=linear_json.header)
        pq.write_table(table, path, **kwargs)

    @staticmethod
    def automatic_type_conversion(row: list[str]) -> list[Any]:
        """Converts a row of strings to the most appropriate type.

        Args:
            row (list[str]): The row of strings to convert.

        Returns:
            list[Any]: The converted row.
        """
        converted_row = []
        for col in row:
            try:
                value = ast.literal_eval(col)
            except (ValueError, SyntaxError):
                value = None if col == "" else col
            converted_row.append(value)
        return converted_row

    @classmethod
    def from_csv(cls, path: str) -> "JSONParser":
        """Loads a JSON object from a CSV file.

        Args:
            path (str): The path to load the CSV file from.

        Returns:
            JSONParser: The JSONParser object.
        """
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(
                f,
                quotechar='"',
                delimiter=",",
                quoting=csv.QUOTE_MINIMAL,
                skipinitialspace=True,
            )
            header = next(reader)
            data = [JSONParser.automatic_type_conversion(row) for row in reader]
        delinearized_data = [delinearize_json(header, row) for row in data]
        return cls(delinearized_data)

    @classmethod
    def from_json(cls, path: str) -> "JSONParser":
        """Loads a JSON object from a JSON file.

        Args:
            path (str): The path to load the JSON file from.

        Returns:
            JSONParser: The JSONParser object.
        """
        with open(path, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    @classmethod
    def from_gzipped_json(cls, path: str) -> "JSONParser":
        """Loads a JSON object from a gzipped JSON file.

        Args:
            path (str): The path to load the gzipped JSON file from.

        Returns:
            JSONParser: The JSONParser object.
        """
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return cls(json.load(f))

    @classmethod
    def from_parquet(cls, path: str) -> "JSONParser":
        """Loads a JSON object from a Parquet file.

        Args:
            path (str): The path to load the Parquet file from.

        Raises:
            ImportError: If the parquet extra is not installed.

        Returns:
            JSONParser: The JSONParser object.
        """
        try:
            import numpy as np
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError(
                "parquet format requires the [parquet] extra to be installed. "
                'Try "pip install splatnet3_scraper[parquet]" or "poetry '
                'install --extras parquet" if you are developing.'
            )
        table = pq.read_table(path)
        data = [table.column(i).to_numpy() for i in range(len(table.columns))]
        out_data = np.array(data).T
        header = [field.name for field in table.schema]
        return cls(delinearize_json(header, out_data.tolist()))
