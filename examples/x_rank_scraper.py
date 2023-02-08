import sqlite3
import time
from typing import Any

from splatnet3_scraper import SplatNet_Query
from splatnet3_scraper.query import QueryResponse


class XRankScraper:
    """Scrapes X Ranking data from SplatNet 3."""

    query = "XRankingQuery"
    modes = ["Ar", "Cl", "Gl", "Lf"]
    current_season_path = ("xRanking", "currentSeason", "id")
    detailed_x_query = "DetailTabViewXRanking%sRefetchQuery"
    detailed_weapon_query = "DetailTabViewWeaponTops%sRefetchQuery"

    def __init__(self, scraper: SplatNet_Query, db_path: str = None) -> None:
        self.scraper = scraper
        self.db_path = db_path if db_path else "x_rank.db"

    def end_cursor_path_x_rank(self, mode: str) -> tuple[str, ...]:
        """Gets the path to the end cursor for the given mode.

        Args:
            mode (str): The mode to get the path for.

        Returns:
            str: The path to the end cursor.
        """
        return ("node", f"xRanking{mode}", "pageInfo", "endCursor")

    def get_current_season(self) -> str:
        """Gets the current season ID.

        Returns:
            str: The current season ID.
        """
        response = self.scraper.query(self.query)
        return response[self.current_season_path]

    def get_detailed_data(
        self,
        season_id: str,
        mode: str,
        page: int,
        cursor: str,
        weapons: bool = False,
    ) -> QueryResponse:
        """Gets the detailed data for the given season, mode, page, and cursor.

        Args:
            season_id (str): The season ID.
            mode (str): The mode.
            page (int): The page.
            cursor (str): The cursor.
            weapons (bool): Whether to get weapon data. Defaults to False.

        Returns:
            QueryResponse: The detailed data.
        """
        variables = {
            "id": season_id,
            "mode": mode,
            "page": page,
            "cursor": cursor,
        }
        base_query = (
            self.detailed_weapon_query if weapons else self.detailed_x_query
        )
        detailed_query = base_query % mode
        response = self.scraper.query(detailed_query, variables=variables)
        return response

    def parse_player_data(self, data: QueryResponse) -> dict[str, Any]:
        """Parses the player data from the given QueryResponse.

        Args:
            data (QueryResponse): The data to parse.

        Returns:
            dict[str, Any]: The parsed data. Additional keys can be added by
                simply adding their paths to the dict along with the key name.
        """
        player_data = {
            "id": data["id"],
            "name": data["name"],
            "name_id": data["nameId"],
            "rank": data["rank"],
            "x_power": data["xPower"],
            "weapon": data["weapon", "name"],
            "weapon_id": data["weapon", "id"],
            "weapon_sub": data["weapon", "subWeapon", "name"],
            "weapon_sub_id": data["weapon", "subWeapon", "id"],
            "weapon_special": data["weapon", "specialWeapon", "name"],
            "weapon_special_id": data["weapon", "specialWeapon", "id"],
        }
        return player_data

    def parse_players_in_mode(
        self, data: QueryResponse, mode: str
    ) -> list[dict[str, Any]]:
        """Given the data for a mode, parses the player data and adds the mode
        to each player.

        Args:
            data (QueryResponse): The data to parse.
            mode (str): The mode.

        Returns:
            list[dict[str, Any]]: The parsed player data.
        """
        players = []
        for player_node in data["edges"]:
            player_data = self.parse_player_data(player_node["node"])
            player_data["mode"] = mode
            players.append(player_data)
        return players

    def scrape_all_players_in_mode(
        self, season_id: str, mode: str
    ) -> list[dict[str, Any]]:
        """Scrapes all players in the given mode.

        Args:
            season_id (str): The season ID.
            mode (str): The mode.

        Returns:
            list[dict[str, Any]]: The scraped player data.
        """
        players = []
        for page in range(1, 6):
            has_next_page = True
            cursor = None
            while has_next_page:
                response = self.get_detailed_data(
                    season_id=season_id,
                    mode=mode,
                    page=page,
                    cursor=cursor,
                )
                subresponse = response["node", f"xRanking{mode}"]
                players.extend(self.parse_players_in_mode(subresponse, mode))

                has_next_page = subresponse["pageInfo", "hasNextPage"]
                cursor = subresponse["pageInfo", "endCursor"]
        return players

    def scrape_all_players_in_season(
        self, season_id: str
    ) -> list[dict[str, Any]]:
        """Scrapes all players in the given season.

        Args:
            season_id (str): The season ID.

        Returns:
            list[dict[str, Any]]: The scraped player data.
        """
        players = []
        for mode in self.modes:
            players.extend(self.scrape_all_players_in_mode(season_id, mode))
        return players

    def scrape_all_players_current_season(self) -> list[dict[str, Any]]:
        """Scrapes all players in the current season.

        Returns:
            list[dict[str, Any]]: The scraped player data.
        """
        season_id = self.get_current_season()
        timestamp = time.time()
        players = self.scrape_all_players_in_season(season_id)
        for player in players:
            player["timestamp"] = timestamp
        return players

    def save_to_db(self, players: list[dict[str, Any]]) -> None:
        """Saves the given player data to an SQLite database.

        Args:
            players (list[dict[str, Any]]): The player data to save.
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                "CREATE TABLE IF NOT EXISTS "
                "players ("
                "id, name, name_id, rank, x_power, weapon, "
                "weapon_id, weapon_sub, weapon_sub_id, "
                "weapon_special, weapon_special_id, mode, "
                "timestamp)"
            )
            c.executemany(
                "INSERT INTO players VALUES "
                "(:id, :name, :name_id, :rank, :x_power, :weapon, "
                ":weapon_id, :weapon_sub, :weapon_sub_id, "
                ":weapon_special, :weapon_special_id, :mode, "
                ":timestamp)",
                players,
            )
            conn.commit()
