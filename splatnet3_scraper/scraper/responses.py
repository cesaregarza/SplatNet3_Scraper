from typing import Any, Literal, overload

from splatnet3_scraper.scraper.json_parser import JSONParser


class QueryResponse:
    """Represents a response from the API. This is a thin wrapper around the
    JSONParser class.
    """

    def __init__(
        self,
        data: dict[str, Any] | list[dict[str, Any]],
        additional_data: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> None:
        """Initializes a QueryResponse.

        Args:
            data (dict[str, Any]): The data from the response.
            additional_data (list[dict[str, Any]] | None): Any additional data,
                useful for complex queries that require multiple requests.
                Defaults to None.
        """
        self._data = data
        self._additional_data = additional_data

    @property
    def data(self) -> JSONParser:
        """The JSONParser object containing the data.

        Returns:
            JSONParser: The data.
        """
        return JSONParser(self._data)

    @property
    def additional_data(self) -> JSONParser:
        """JSONParser containing any additional data. Intended to contain data
            from multiple requests, such as detailed battle data.

        Raises:
            AttributeError: If there is no additional data.

        Returns:
            JSONParser: The additional data.
        """
        if self._additional_data is None:
            raise AttributeError("No additional data")
        return JSONParser(self._additional_data)

    def __repr__(self) -> str:
        detail_str = "+" if self._additional_data is not None else ""
        return f"QueryResponse{detail_str}()"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QueryResponse):
            return False
        return (
            self._data == other._data
            and self._additional_data == other._additional_data
        )

    def __getitem__(
        self, key: str | int | tuple[str | int, ...]
    ) -> "QueryResponse":
        if isinstance(key, tuple):
            for k in key:
                self = self[k]
            return self

        data = self._data[key]  # type: ignore
        if isinstance(data, (dict, list)):
            return QueryResponse(data)
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
