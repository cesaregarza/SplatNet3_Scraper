from typing import Any
import json
from splatnet3_scraper.utils import linearize_json


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

    def __hash_header(self, header: list[str]) -> str:
        """Helper method to hash a header.

        Args:
            header (list[str]): The header to hash.

        Returns:
            str: The hashed header.
        """
        header_tuple = tuple(header)
        return str(hash(header_tuple))

    def to_json(self, path: str, detailed_path: str | None = None) -> None:
        """Saves the response to a file. If the response contains detailed data,
        it will be saved to a separate file.

        Args:
            path (str): The path to save the response to.
        """
        with open(path, "w") as f:
            json.dump(self.summary, f, indent=4)

        if self.detailed is not None:
            with open(detailed_path, "w") as f:
                json.dump(self.detailed, f, indent=4)

    def __to_csv(self, object: dict[str, Any]) -> tuple[str, str]:
        """Helper method to linearize a JSON object and turn it into a string
        that can be written to a CSV file.

        Args:
            object (dict[str, Any]): JSON object to convert.

        Returns:
            tuple[str, str]: The header and data as a string.
        """
        header, data = linearize_json(object)
        header_str = ",".join(header)
        data_str = ",".join([str(x) for x in data])
        return header_str, data_str

    def __detailed_to_csv(
        self, objects: list[dict[str, Any]]
    ) -> tuple[str, str]:
        """Helper method to linearize a list of JSON objects to turn into a
        string that can be written to a CSV file. It will group the objects by
        their headers.

        Args:
            object (dict[str, Any]): JSON object to convert.

        Returns:
            tuple[str, str]: The header and data as a string.
        """
        jsons: dict[str, list[str]] = {}
        for obj in objects:
            header, data = self.__to_csv(obj)
            hashed_header = self.__hash_header(header)
            if hashed_header not in jsons:
                jsons[hashed_header] = []
            jsons[hashed_header].append(data)

    def to_csv(self, path: str, detailed_path: str | None = None) -> None:
        """Saves the response to a CSV file. If the response contains detailed
        data, it will be saved to a separate file.

        Args:
            path (str): The path to save the response to.
        """
        header, data = self.__to_csv(self.summary)
        with open(path, "w") as f:
            f.write(header + "\n")
            f.write(data + "\n")

        if detailed_path is None:
            return

        if self.detailed is None:
            raise ValueError("No detailed data to save.")

        header, data = self.__to_csv(self.detailed[0])
        with open(detailed_path, "w") as f:
            f.write(header + "\n")
            f.write(data + "\n")
            for obj in self.detailed[1:]:
                _, data = self.__to_csv(obj)
                f.write(data + "\n")
