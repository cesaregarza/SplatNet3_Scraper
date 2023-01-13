from dataclasses import dataclass

from splatnet3_scraper.schemas.base import JSONDataClass
from splatnet3_scraper.schemas.overview.coop import CoopResultSchema
from splatnet3_scraper.schemas.overview.history_groups import (
    anarchyHistoryGroupsSchema,
    regularHistoryGroupsSchema,
)
from splatnet3_scraper.schemas.overview.history_groups_only_first import (
    historyGroupsOnlyFirstSchema,
)


@dataclass(repr=False)
class SummarySchema(JSONDataClass):
    assistAverage: float
    deathAverage: float
    killAverage: float
    lose: int
    perUnitTimeMinute: int
    specialAverage: float
    win: int


@dataclass(repr=False)
class anarchyBattleHistorySchema(JSONDataClass):
    historyGroups: anarchyHistoryGroupsSchema
    historyGroupsOnlyFirst: historyGroupsOnlyFirstSchema
    summary: SummarySchema


@dataclass(repr=False)
class regularBattleHistorySchema(JSONDataClass):
    historyGroups: regularHistoryGroupsSchema
    historyGroupsOnlyFirst: historyGroupsOnlyFirstSchema
    summary: SummarySchema


class OverviewSchema(JSONDataClass):
    def __init__(self, overview_json: list[dict]) -> None:
        def json_idx(idx: int) -> dict:
            map = {
                0: "regularBattleHistories",
                1: "bankaraBattleHistories",
                2: "privateBattleHistories",
                3: "coopResult",
            }
            print(idx, map[idx])
            return overview_json[idx]["data"][map[idx]]

        self.regularBattleHistories = regularBattleHistorySchema(**json_idx(0))
        self.anarchyBattleHistories = anarchyBattleHistorySchema(**json_idx(1))
        self.privateBattleHistories = regularBattleHistorySchema(**json_idx(2))
        self.coopResults = CoopResultSchema(**json_idx(3))
