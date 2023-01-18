from typing import Any

from splatnet3_scraper.scraper.json_parser import JSONParser


class QueryResponse:
    """Represents a response from the API. This is a thin wrapper around the
    JSONParser class.
    """

    def __init__(
        self,
        summary: dict[str, Any],
        detailed: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initializes a QueryResponse.

        Args:
            summary (dict[str, Any]): The summary data from the response.
            detailed (list[dict[str, Any]] | None): The detailed data from the
                response. Defaults to None.
        """
        self._summary = JSONParser(summary)
        self._detailed = JSONParser(detailed) if detailed is not None else None

    @property
    def summary(self) -> JSONParser:
        """JSONParser of the summary data.

        Returns:
            JSONParser: The summary data.
        """
        return self._summary

    @property
    def detailed(self) -> JSONParser:
        """JSONParser of the detailed data. If there is no detailed data, this
        will raise an AttributeError.

        Raises:
            AttributeError: If there is no detailed data.

        Returns:
            JSONParser: The detailed data.
        """
        if self._detailed is None:
            raise AttributeError("No detailed data")
        return self._detailed

    def __repr__(self) -> str:
        detail_str = "Detailed" if self._detailed is not None else ""
        return f"QueryResponse({detail_str})"
