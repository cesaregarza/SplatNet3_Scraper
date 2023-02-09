from datetime import datetime
from typing import Any, Literal, TypedDict, overload

from splatnet3_scraper.query.json_parser import JSONParser


class MetaData(TypedDict, total=False):
    query: str
    timestamp: float


class QueryResponse:
    """Represents a response from the API. This class provides convenience
    methods for interacting with the returned data. It also provides a
    JSONParser object for more advanced usage, if needed.
    """

    def __init__(
        self,
        data: dict[str, Any] | list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
        *args,
        query: str | None = None,
        timestamp: float | None = None,
    ) -> None:
        """Initializes a QueryResponse.

        Args:
            data (dict[str, Any]): The data from the response.
            metadata (dict[str, Any] | None): The metadata from the response.
                Possible keys are "query" and "timestamp". Defaults to None.
            *args: These are ignored.
            query (str | None): The query that was used to get the data. If
                provided, it will override the metadata dictionary. Defaults to
                None.
            timestamp (float | None): The timestamp of the response. If
                provided, it will override the metadata dictionary. Defaults to
                None.
        """
        self._data = data

        self._metadata = self.__parse_metadata(metadata)

    def __parse_metadata(self, metadata: dict) -> MetaData | None:
        if metadata is None:
            return None

        annotations = MetaData.__annotations__
        _metadata = {}
        for key, value in metadata.items():
            if key in annotations:
                _metadata[key] = value
        if len(_metadata) == 0:
            return None
        return MetaData(_metadata)

    @property
    def data(self) -> dict[str, Any] | list[dict[str, Any]]:
        """The data from the response.

        Returns:
            dict[str, Any]: The data.
        """
        return self._data

    @property
    def metadata(self) -> MetaData:
        """The metadata from the response.

        Raises:
            ValueError: If no metadata was provided at initialization.

        Returns:
            dict[str, Any]: The metadata.
        """
        if self._metadata is None:
            raise ValueError("No metadata was provided.")
        return self._metadata

    @property
    def query(self) -> str:
        """The query that was used to get the data.

        Raises:
            ValueError: If no metadata was provided at initialization.

        Returns:
            str: The query.
        """
        if self._metadata is None:
            raise ValueError("No metadata was provided.")
        try:
            return self._metadata["query"]
        except KeyError:
            raise ValueError("No query was provided.")

    @property
    def timestamp_raw(self) -> float:
        """The timestamp of the response, as a float.

        Raises:
            ValueError: If no metadata was provided at initialization.

        Returns:
            float: The timestamp.
        """
        if self._metadata is None:
            raise ValueError("No metadata was provided.")
        try:
            return self._metadata["timestamp"]
        except KeyError:
            raise ValueError("No timestamp was provided.")

    @property
    def timestamp(self) -> datetime:
        """The timestamp of the response, as a datetime object.

        Returns:
            datetime: The timestamp.
        """
        return datetime.fromtimestamp(self.timestamp_raw)

    def parse_json(self) -> JSONParser:
        """The JSONParser object containing the data.

        Returns:
            JSONParser: The data.
        """
        return JSONParser(self._data)

    def __repr__(self) -> str:
        out_str = "QueryResponse("
        if self._metadata is None:
            return out_str + ")"

        spacing = " " * len(out_str)
        for key, value in self._metadata.items():
            # Intercept if key is "timestamp" and convert to datetime
            if key == "timestamp":
                out_value = datetime.fromtimestamp(value).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            elif isinstance(value, str):
                out_value = value if len(value) < 20 else value[:20] + "..."
            elif isinstance(value, float):
                out_value = f"{value:.2f}"
            else:
                out_value = str(value)

            out_str += spacing + f"{key}={out_value},\n"

        return out_str[:-2] + ")"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QueryResponse):
            return False
        return self._data == other._data and self._metadata == other._metadata

    def __getitem__(
        self, key: str | int | tuple[str | int, ...]
    ) -> "QueryResponse":
        if isinstance(key, tuple):
            for k in key:
                self = self[k]
            return self

        data = self._data[key]  # type: ignore
        if isinstance(data, (dict, list)):
            return QueryResponse(data, metadata=self._metadata)
        return data

    def keys(self) -> list[str]:
        """Returns a list of keys in the data.

        Returns:
            list[str]: The keys in the data.
        """
        return list(self._data.keys())

    def values(self) -> list[Any]:
        """Returns a list of values in the data.

        Returns:
            list[Any]: The values in the data.
        """
        return list(self._data.values())

    def items(self) -> list[tuple[str, Any]]:
        """Returns a list of items in the data.

        Returns:
            list[tuple[str, Any]]: The items in the data.
        """
        return list(self._data.items())

    def __iter__(self) -> iter:
        return iter(self._data)

    @overload
    def show(self, return_value: bool = Literal[False]) -> None:
        ...

    @overload
    def show(self, return_value: bool = Literal[True]) -> dict[str, Any]:
        ...

    @overload
    def show(self, return_value: bool = ...) -> None | dict[str, Any]:
        ...

    def show(self, return_value: bool = False) -> None | dict[str, Any]:
        """Prints the data to the console. If return_value is True, returns the
        data as a dict instead.

        Args:
            return_value (bool): Whether to return the data as a dict. If True,
                the data will be returned instead of printed. Defaults to False.

        Returns:
            None | dict[str, Any]: The data as a dict if return_value is True,
                otherwise None.
        """
        if return_value:
            return self._data
        print(self._data)
