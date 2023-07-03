import logging
from typing import Callable, Literal, cast, overload

from splatnet3_scraper.query import QueryHandler, QueryResponse
from splatnet3_scraper.scraper.query_map import QueryMap


class SplatNet_Scraper:
    """This class offers a user-level interface for pulling data from SplatNet
    3. It is built upon the QueryHandler class and provides a top-level
    API that orchestrates multiple queries together to reduce the amount of work
    needed to pull data that users are likely to want.
    """

    def __init__(self, query_handler: QueryHandler) -> None:
        """Initializes a SplatNet_Scraper.

        Args:
            query_handler (QueryHandler): The query handler to use.
        """
        self._query_handler = query_handler
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def from_session_token(session_token: str) -> "SplatNet_Scraper":
        """Creates a SplatNet_Scraper instance using the given session token.

        Args:
            session_token (str): The session token to use.

        Returns:
            SplatNet_Scraper: The SplatNet_Scraper instance.
        """
        query_handler = QueryHandler.from_session_token(session_token)
        return SplatNet_Scraper(query_handler)

    @staticmethod
    def from_config_file(config_path: str | None = None) -> "SplatNet_Scraper":
        """Creates a SplatNet_Scraper instance using the given config file.

        Args:
            config_path (str | None): The path to the config file. If None, it
                will look for ".splatnet3_scraper" in the current working
                directory.

        Returns:
            SplatNet_Scraper: The SplatNet_Scraper instance.
        """
        query_handler = QueryHandler.from_config_file(config_path)
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
        query_handler = QueryHandler.from_env()
        return SplatNet_Scraper(query_handler)

    @staticmethod
    def from_s3s_config(config_path: str) -> "SplatNet_Scraper":
        """Creates a SplatNet_Scraper instance using the config file from s3s.

        Args:
            config_path (str): The path to the config file.

        Returns:
            SplatNet_Scraper: The SplatNet_Scraper instance.
        """
        query_handler = QueryHandler.from_s3s_config(config_path)
        return SplatNet_Scraper(query_handler)

    def __query(self, query: str, variables: dict = {}) -> QueryResponse:
        """Convenience function for querying.

        Args:
            query (str): The query to run.
            variables (dict): The variables to pass to the query. Defaults to
                an empty dict.

        Returns:
            QueryResponse: The QueryResponse.
        """
        return self._query_handler.query(query, variables)

    def __detailed_vs_or_coop(
        self,
        query: str,
        limit: int | None = None,
        existing_ids: list[str] | str | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> tuple[QueryResponse, list[QueryResponse]]:
        """Gets the detailed results for a vs battle or coop battle.

        Args:
            query (str): The query to run.
            limit (int | None): The maximum number of battles to get. If None,
                it will get all battles. Defaults to None.
            existing_ids (list[str] | str | None): The existing IDs to check
                against. If a string is passed, it will return the results
                upon finding the first match. If a list is passed, it will
                return the results of all matches not in the list. If None,
                it will return all results. Defaults to None.
            progress_callback (Callable[[int, int], None] | None): A callback
                function that will be called with the current index and the
                total number of battles. Defaults to None.

        Raises:
            ValueError: If the query is not a vs battle or coop battle.

        Returns:
            tuple:
                QueryResponse: The summary query response.
                list[QueryResponse]: The list of detailed query responses
                    associated with each battle until the limit is reached.
        """
        if query not in (
            QueryMap.SALMON,
            QueryMap.TURF,
            QueryMap.ANARCHY,
            QueryMap.XBATTLE,
            QueryMap.PRIVATE,
        ):
            raise ValueError(f"Invalid query: {query}")

        if query in (QueryMap.SALMON, QueryMap.SALMON_DETAIL):
            detail_query = QueryMap.SALMON_DETAIL
            variable_name = "coopHistoryDetailId"
        else:
            detail_query = QueryMap.VS_DETAIL
            variable_name = "vsResultId"

        _limit = -1 if limit is None else limit
        self.logger.info(f"Limit set to {_limit}")

        # Get the list of battles
        summary_query = self.__query(query)

        # Top level key depends on the game mode, but there is only one.
        top_level_key = summary_query.keys()[0]
        history_groups = summary_query[top_level_key, "historyGroups", "nodes"]
        out: list[QueryResponse] = []
        queue: list[str] = []
        idx = 0
        break_early = False

        for group in history_groups:
            group = cast(QueryResponse, group)
            if break_early:
                break
            for game in group["historyDetails", "nodes"]:
                game = cast(QueryResponse, game)
                if idx == _limit:
                    break_early = True
                    break
                idx += 1
                game_id = cast(str, game["id"])

                if isinstance(existing_ids, str):
                    if game_id == existing_ids:
                        break_early = True
                        break
                elif isinstance(existing_ids, list):
                    if game_id in existing_ids:
                        idx -= 1
                        continue

                variables = {variable_name: game_id}
                queue.append(game_id)

        self.logger.info(f"Queue length: {len(queue)}")
        if progress_callback is not None:
            progress_callback(0, len(queue))
        for idx, game_id in enumerate(queue):
            self.logger.info(f"Getting game {idx + 1} of {len(queue)}")
            variables = {variable_name: game_id}
            detailed_game = self.__query(detail_query, variables)
            out.append(detailed_game)
            if progress_callback is not None:
                progress_callback(idx + 1, len(queue))
        return summary_query, out

    @overload
    def get_vs_battles(
        self,
        mode: str,
        detail: Literal[False],
        limit: int | None = None,
        existing_ids: list[str] | str | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> QueryResponse:
        ...

    @overload
    def get_vs_battles(
        self,
        mode: str,
        detail: Literal[True],
        limit: int | None = None,
        existing_ids: list[str] | str | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> tuple[QueryResponse, list[QueryResponse]]:
        ...

    @overload
    def get_vs_battles(
        self,
        mode: str,
        detail: bool = False,
        limit: int | None = None,
        existing_ids: list[str] | str | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> QueryResponse | tuple[QueryResponse, list[QueryResponse]]:
        ...

    def get_vs_battles(
        self,
        mode: str,
        detail: bool = False,
        limit: int | None = None,
        existing_ids: list[str] | str | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> QueryResponse | tuple[QueryResponse, list[QueryResponse]]:
        """Gets the vs battles.

        Args:
            mode (str): The mode to get the battles for. Some values are:
                "turf", "anarchy", "xbattle", "private",
            detail (bool): Whether to get the detailed results or not.
                Defaults to False.
            limit (int | None): The maximum number of battles to get. If None,
                it will get all battles. Defaults to None.
            existing_ids (list[str] | str | None): The existing IDs to check
                against. If a string is passed, it will return the results
                upon finding the first match. If a list is passed, it will
                return the results of all matches not in the list. If None,
                it will return all results. Defaults to None.
            progress_callback (Callable[[int, int], None] | None): A callback
                function that will be called with the current index and the
                total number of battles. Defaults to None.

        Raises:
            ValueError: If the mode is not valid.

        Returns:
            QueryResponse : The summary query response, returned regardless of
                the value of detail.
            (list[QueryResponse]): The list of detailed query responses
                associated with each battle until the limit is reached. Only
                returned if detail is True, along with the summary query
                response.
        """
        mapped_query = QueryMap.get(mode)
        if mapped_query == QueryMap.SALMON:
            raise ValueError("Use get_coop_battles for salmon run battles.")

        if mapped_query in (
            QueryMap.TURF_DETAIL,
            QueryMap.ANARCHY_DETAIL,
            QueryMap.XBATTLE_DETAIL,
            QueryMap.PRIVATE_DETAIL,
        ):
            non_detail_map = {
                QueryMap.TURF_DETAIL: QueryMap.TURF,
                QueryMap.ANARCHY_DETAIL: QueryMap.ANARCHY,
                QueryMap.XBATTLE_DETAIL: QueryMap.XBATTLE,
                QueryMap.PRIVATE_DETAIL: QueryMap.PRIVATE,
            }
            mapped_query = non_detail_map[mapped_query]
            detail = True

        if mapped_query not in (
            QueryMap.TURF,
            QueryMap.ANARCHY,
            QueryMap.XBATTLE,
            QueryMap.PRIVATE,
        ):
            raise ValueError(f"Invalid mode: {mode}")

        if detail:
            return self.__detailed_vs_or_coop(
                mapped_query, limit, existing_ids, progress_callback
            )
        else:
            return self.__query(mapped_query)
