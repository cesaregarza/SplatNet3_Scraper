from dataclasses import dataclass

from splatnet3_scraper.schemas.base import JSONDataClass
from splatnet3_scraper.schemas.general import (
    colorSchema,
    imageSchema,
    nameplateSchema,
    weaponSchema,
)


@dataclass(repr=False)
class rankArraySchema(JSONDataClass):
    id: str
    name: str
    rank: int
    festPower: float
    weapon: weaponSchema
    _isPlayer: str
    byname: str
    nameId: str
    nameplate: nameplateSchema


@dataclass(repr=False)
class rankingHoldersSchema(JSONDataClass):
    nodes: list[rankArraySchema]


@dataclass(repr=False)
class resultFieldSchema(JSONDataClass):
    rankingHolders: rankingHoldersSchema


@dataclass(repr=False)
class splatfestTeamSchema(JSONDataClass):
    color: colorSchema
    id: str
    image: imageSchema
    result: resultFieldSchema
    teamName: str

    @property
    def players(self) -> list[rankArraySchema]:
        """Get the players on this team.

        Returns:
            list[rankArraySchema]: The players on this team.
        """
        return self["result", "rankingHolders", "nodes"]

    def get_table(self) -> list[dict]:
        """Gets the table of the team's ranking holders.

        Returns:
            list[dict]: A list of dictionaries containing the ranking holders'
                names, weapons, and fest power.
        """
        out = []
        for player in self.players:
            weapon: weaponSchema = player["weapon"].get_simple_name()
            out.append(
                {
                    "team": self["teamName"],
                    "player_name": player["name"],
                    "weapon": weapon["name"],
                    "sub": weapon["sub"],
                    "special": weapon["special"],
                    "fest_power": player["festPower"],
                    "byname": player["byname"],
                }
            )
        return out


@dataclass(repr=False)
class festSchema(JSONDataClass):
    _typename: str
    id: str
    lang: str
    teams: list[splatfestTeamSchema]


@dataclass(repr=False)
class splatfestResults(JSONDataClass):
    fest: festSchema


@dataclass(repr=False)
class splatfestResultsSchema(JSONDataClass):
    data: splatfestResults

    def get_teams(self) -> list[str]:
        """Gets the team names from the results.

        Returns:
            list[str]: The team names.
        """
        return [team["teamName"] for team in self["data", "fest", "teams"]]
