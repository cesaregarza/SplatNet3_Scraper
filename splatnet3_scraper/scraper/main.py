from typing import cast

from splatnet3_scraper.query import QueryResponse, SplatNet_QueryHandler
from splatnet3_scraper.scraper.query_map import QueryMap


class SplatNet_Scraper:
    """This class offers a user-level interface for pulling data from SplatNet
    3. It is built upon the SplatNet_QueryHandler class and provides a top-level
    API that orchestrates multiple queries together to reduce the amount of work
    needed to pull data that users are likely to want.
    """

    def __init__(self, query_handler: SplatNet_QueryHandler) -> None:
        """Initializes a SplatNet_Scraper.

        Args:
            query_handler (SplatNet_QueryHandler): The query handler to use.
        """
        self._query_handler = query_handler

    @staticmethod
    def from_session_token(session_token: str) -> "SplatNet_Scraper":
        """Creates a SplatNet_Scraper instance using the given session token.

        Args:
            session_token (str): The session token to use.

        Returns:
            SplatNet_Scraper: The SplatNet_Scraper instance.
        """
        query_handler = SplatNet_QueryHandler.from_session_token(session_token)
        return SplatNet_Scraper(query_handler)

    @staticmethod
    def from_config(config_path: str | None = None) -> "SplatNet_Scraper":
        """Creates a SplatNet_Scraper instance using the given config file.

        Args:
            config_path (str | None): The path to the config file. If None, it
                will look for ".splatnet3_scraper" in the current working
                directory.

        Returns:
            SplatNet_Scraper: The SplatNet_Scraper instance.
        """
        query_handler = SplatNet_QueryHandler.from_config_file(config_path)
        return SplatNet_Scraper(query_handler)

    @staticmethod
    def from_env() -> "SplatNet_Scraper":
        """Creates a SplatNet_Scraper instance using the environment variables.

        Environment variables:
            SN3S_SESSION_TOKEN: The session token to use.
            SN3S_GTOKEN: The gtoken to use.
            SN3S_BULLET_TOKEN: The bullet token to use.

        Returns:
            SplatNet_Scraper: The SplatNet_Scraper instance.
        """
        query_handler = SplatNet_QueryHandler.from_env()
        return SplatNet_Scraper(query_handler)

    @staticmethod
    def from_s3s_config(config_path: str) -> "SplatNet_Scraper":
        """Creates a SplatNet_Scraper instance using the config file from s3s.

        Args:
            config_path (str): The path to the config file.

        Returns:
            SplatNet_Scraper: The SplatNet_Scraper instance.
        """
        query_handler = SplatNet_QueryHandler.from_s3s_config(config_path)
        return SplatNet_Scraper(query_handler)

    def __query(self, query: str, variables: dict = {}) -> QueryResponse:
        """Convenience function for querying.

        Args:
            query (str): The query to run.

        Returns:
            QueryResponse: The QueryResponse.
        """
        return self._query_handler.query(query, variables)

    def __detailed_vs_or_coop(
        self, query: str, coop: bool, limit: int | None = None
    ) -> tuple[QueryResponse, list[QueryResponse]]:
        """Gets the detailed results for a vs battle or coop battle.

        Args:
            coop (bool): Whether to get coop battles or not.
            limit (int | None): The maximum number of battles to get. If None,
                it will get all battles. Defaults to None.

        Returns:
            tuple:
                QueryResponse: The summary query response.
                list[QueryResponse]: The list of detailed query responses
                    associated with each battle until the limit is reached.
        """
        detail_query = QueryMap.SALMON_DETAIL if coop else QueryMap.VS_DETAIL
        variable_name = "coopHistoryDetailId" if coop else "vsHistoryDetailId"

        _limit = -1 if limit is None else limit

        # Get the list of battles
        summary_query = self.__query(query)

        # Top level key depends on the game mode, but there is only one.
        top_level_key = summary_query.keys()[0]
        history_groups = summary_query[top_level_key, "historyGroups", "nodes"]
        out: list[QueryResponse] = []
        idx = 0

        for group in history_groups:
            group = cast(QueryResponse, group)
            for game in group["historyDetails", "nodes"]:
                game = cast(QueryResponse, game)
                if idx == _limit:
                    return out
                idx += 1
                game_id = game["id"]
                variables = {variable_name: game_id}
                detailed_game = self.__query(detail_query, variables)
                out.append(detailed_game)

        return summary_query, out
