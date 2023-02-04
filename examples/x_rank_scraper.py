import time
from typing import Any

import pandas as pd

from splatnet3_scraper import SplatNet3_Scraper
from splatnet3_scraper.scraper import QueryResponse


class XRankScraper:
    query = "xRankingQuery"
    modes = ["Ar", "Cl", "Gl", "Lf"]
    current_season_path = ("xRanking", "currentSeason", "id")

    def __init__(self, scraper: SplatNet3_Scraper) -> None:
        self.scraper = scraper
    
    def end_cursor_path_x_rank(self, mode: str, tab: bool = False) -> str:
        return ("node", f"xRanking{mode}", "pageInfo", "endCursor")

    def get_current_season(self) -> str:
        response = self.scraper.query(self.query)
        return response[self.current_season_path]

    def get_detailed_data(self, id: str, mode: str, page: int, cursor: str) -> QueryResponse:
        variables = {
            "id": id,
            "mode": mode,
            "page": page,
            "cursor": cursor,
        }
        response = self.scraper.query(self.detailed_query, variables=variables)
        return response

    def get_x_rank_data(self) -> QueryResponse:
        response = self.scraper.query(self.query)
        return response

    def parse_player_data(self, data: QueryResponse) -> dict[str, Any]:
        player_data = {
            "id": data["id"],
            "name": data["name"],
            "name_id": data["nameId"],
            "rank": data["rank"],
            "rank_diff": data["rankDiff"],
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

    def parse_players(self, data: QueryResponse) -> list[dict[str, Any]]:
        players = []
        for mode in self.modes:

            players.extend(self.parse_players_in_mode(data[mode], mode))
        return players
