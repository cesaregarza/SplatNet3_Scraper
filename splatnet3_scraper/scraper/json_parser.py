import hashlib
import json
from typing import Any, Literal, overload

from splatnet3_scraper.utils import delinearize_json, linearize_json


class LinearJSON:
    """Class containing methods for linearized JSON objects."""

    def __init__(self, header: list[str], data: list[list]) -> None:
        """Initializes a LinearJSON.

        Args:
            header (list[str]): The header of the JSON object.
            data (list[Any]): The data of the JSON object.
        """
        self.header = header
        self.data = data
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
    def hash(obj: list[str]) -> str:
        """Returns the hash of the header.

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
        out = {"data": []}
        for row in self.data:
            out["data"].append(delinearize_json(self.header, row))
        return out

    def __hash__(self) -> int:
        """Returns the hash of the header.

        Returns:
            int: The hash of the header.
        """
        return self.hash(self.header)

    def __eq__(self, other: object) -> bool:
        """Returns whether the other object is equal to this object.

        Args:
            other (object): The other object to compare.

        Returns:
            bool: Whether the other object is equal to this object.
        """
        if isinstance(other, LinearJSON):
            return self.header == other.header
        elif isinstance(other, list):
            return self.header == other
        return False

    def __validate(self) -> None:
        """Validates the LinearJSON object."""
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

        Args:
            new_header (list[str]): The new header.
        """
        new_headers = [x for x in new_header if x not in self.header]
        removed_headers = [x for x in self.header if x not in new_header]
        if (not new_headers) and (not removed_headers):
            return
        new_data = []
        for row in self.data:
            new_row = []
            for i, col in enumerate(new_header):
                if col in new_headers:
                    new_row.append(None)
                elif col in removed_headers:
                    # Shouldn't happen, but making the logic explicit
                    continue
                else:
                    new_index = self.header.index(col)
                    new_row.append(row[new_index])
            new_data.append(new_row)
        self.header = new_header
        self.data = new_data

    def __merge_headers(self, other: "LinearJSON") -> list[str]:
        """Merges the headers of this object and the other object.

        Args:
            other (LinearJSON): The other object to merge with.

        Returns:
            list[str]: The new header.
        """
        new_header = set(self.header).union(set(other.header))
        new_header = sorted(new_header, key=lambda x: (len(x), x))
        return new_header

    def append(self, other: "LinearJSON") -> None:
        """Appends a LinearJSON object to this one.

        Args:
            other (LinearJSON): The other LinearJSON object to append.

        Raises:
            ValueError: The other LinearJSON object does not have the same
                header.
        """
        if self.header != other.header:
            new_header = self.__merge_headers(other)
            # New header will have new columns anywhere in the header, so we
            # need to identify the new columns and insert None values for them
            # in the data
            obj_list: list[LinearJSON] = [self, other]
            for obj in obj_list:
                obj.__standardize_new_header(new_header)
        self.data.extend(other.data)

    def transpose(self) -> list[list[Any]]:
        """Transposes the data of the LinearJSON object."""
        return [list(x) for x in zip(*self.data)]

    @overload
    def stringify(
        self, transpose: bool, include_header: Literal[True] = ...
    ) -> tuple[str, str]:
        ...

    @overload
    def stringify(self, transpose: bool, include_header: Literal[False]) -> str:
        ...

    @overload
    def stringify(
        self, transpose: bool, include_header: bool
    ) -> str | tuple[str, str]:
        ...

    def stringify(
        self,
        transpose: bool = False,
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
        data = self.data if not transpose else self.transpose()
        data_str = []
        for row in data:
            data_str.append(",".join([str(x) for x in row]))
        data_str_out = "\n".join(data_str)
        if include_header:
            header_str = ",".join(self.header)
            return header_str, data_str_out
        return data_str_out


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

    @staticmethod
    def stringify(object: dict[str, Any]) -> tuple[str, str]:
        """Helper method to linearize a JSON object and turn it into a string
        that can be written to a CSV file.

        Args:
            object (dict[str, Any]): JSON object to convert.

        Returns:
            tuple[str, str]: The header and data as a string.
        """
        header, data = linearize_json(object)
        header = ",".join(header)
        data = ",".join([str(x) for x in data])
        return header, data

    def __to_linear_json(self) -> LinearJSON:
        """Converts the JSON object to a LinearJSON object.

        Returns:
            LinearJSON: The LinearJSON object.
        """
        header, data = linearize_json(self.data)
        return LinearJSON(header, data)

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
            columnar (bool): Whether to save the data in columnar format.
                Defaults to False.
        """
        linear_json = self.__to_linear_json()
        with open(path, "w") as f:
            header, data = linear_json.stringify()
            f.write(header + "\n")
            f.write(data)

    def to_json(self, path: str, **kwargs) -> None:
        """Saves the JSON object to a JSON file. Any keyword arguments are
        passed to the json.dump method.

        Args:
            path (str): The path to save the JSON file to.
        """
        default_kwargs = {"indent": 4}
        default_kwargs.update(kwargs)
        with open(path, "w") as f:
            json.dump(self.data, f, **default_kwargs)

    def to_parquet(self, path: str, **kwargs) -> None:
        """Saves the JSON object to a Parquet file. Any keyword arguments are
        passed to the pandas.DataFrame.to_parquet method.

        Args:
            path (str): The path to save the Parquet file to.
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
