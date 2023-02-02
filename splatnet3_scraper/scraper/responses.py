from typing import Any

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
