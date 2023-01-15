from typing import Any


class QueryResponse:
    """Represents a response from the API. Contains the raw response as well as
    some methods to help parse the data.
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
        self.summary = summary
        self.detailed = detailed
