import sqlite3
import time
from typing import Any

from splatnet3_scraper import SplatNet3_Scraper
from splatnet3_scraper.scraper import QueryResponse


class XRankScraper:
    query = "XRankingQuery"
    modes = ["Ar", "Cl", "Gl", "Lf"]
    current_season_path = ("xRanking", "currentSeason", "id")
    detailed_x_query = "DetailTabViewXRanking%sRefetchQuery"
    detailed_weapon_query = "DetailTabViewWeaponTops%sRefetchQuery"

    def __init__(self, scraper: SplatNet3_Scraper, db_path: str = None) -> None:
        self.scraper = scraper
        self.db_path = db_path if db_path else "x_rank.db"

    def end_cursor_path_x_rank(self, mode: str, tab: bool = False) -> str:
        return ("node", f"xRanking{mode}", "pageInfo", "endCursor")

    def get_current_season(self) -> str:
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
        players = []
        for player_node in data["edges"]:
            player_data = self.parse_player_data(player_node["node"])
            player_data["mode"] = mode
            players.append(player_data)
        return players

    def scrape_all_players_in_mode(
        self, season_id: str, mode: str
    ) -> list[dict[str, Any]]:
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
        players = []
        for mode in self.modes:
            players.extend(self.scrape_all_players_in_mode(season_id, mode))
        return players

    def scrape_all_players_current_season(self) -> list[dict[str, Any]]:
        season_id = self.get_current_season()
        timestamp = time.time()
        players = self.scrape_all_players_in_season(season_id)
        for player in players:
            player["timestamp"] = timestamp
        return players

    def save_to_db(self, players: list[dict[str, Any]]) -> None:
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
