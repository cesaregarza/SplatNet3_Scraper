from splatnet3_scraper.query import QueryResponse, SplatNet_QueryHandler


class SplatNet_Scraper:
    """This class offers a user-level interface for pulling data from SplatNet
    3. It is built upon the SplatNet_QueryHandler class and provides a top-level API
    that orchestrates multiple queries together to reduce the amount of work
    needed to pull commonly-used data.
    """

    def __init__(self, query_handler: SplatNet_QueryHandler) -> None:
        """Initializes a SplatNet_Scraper.

        Args:
            query_handler (SplatNet_QueryHandler): The query handler to use.
        """
        self._query_handler = query_handler
