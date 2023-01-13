from dataclasses import dataclass

from splatnet3_scraper.schemas.base import JSONDataClass
from splatnet3_scraper.schemas.general import (
    idSchema,
    imageSchema,
    vsModeSchema,
    vsRuleSchema,
    vsStageSchema,
)


@dataclass(repr=False)
class weaponSchema(JSONDataClass):
    image: imageSchema
    name: str
    id: str


@dataclass(repr=False)
class playerSchema(JSONDataClass):
    weapon: weaponSchema
    id: str
    festGrade: int = None


@dataclass(repr=False)
class myTeamResultSchema(JSONDataClass):
    paintPoint: int = None
    paintRatio: float = None
    score: int = None

    def which(self) -> str:
        if self.score is not None:
            return "anarchy"
        elif (self.paintPoint is not None) and (self.paintRatio is not None):
            return "regular"
        else:
            pass


@dataclass(repr=False)
class myTeamSchema(JSONDataClass):
    result: myTeamResultSchema


@dataclass(repr=False)
class bankaraMatchSchema(JSONDataClass):
    earnedUdemaePoint: None = None


@dataclass(repr=False)
class baseHistoryDetailsNodesSchema(JSONDataClass):
    id: str
    vsMode: vsModeSchema
    vsRule: vsRuleSchema
    vsStage: vsStageSchema
    judgement: str
    player: playerSchema
    myTeam: myTeamSchema
    knockout: str


@dataclass(repr=False)
class anarchyHistoryDetailsNodesSchema(baseHistoryDetailsNodesSchema):
    bankaraMatch: bankaraMatchSchema
    udemae: str
    nextHistoryDetail: idSchema = None
    previousHistoryDetail: idSchema = None


@dataclass(repr=False)
class regularHistoryDetailsNodesSchema(baseHistoryDetailsNodesSchema):
    playedTime: str
    nextHistoryDetail: idSchema = None
    previousHistoryDetail: idSchema = None


@dataclass(repr=False)
class anarchyHistoryDetailsSchema(JSONDataClass):
    nodes: list[anarchyHistoryDetailsNodesSchema]


@dataclass(repr=False)
class regularHistoryDetailsSchema(JSONDataClass):
    nodes: list[regularHistoryDetailsNodesSchema]


@dataclass(repr=False)
class bankaraMatchChallengeSchema(JSONDataClass):
    winCount: int
    loseCount: int
    maxWinCount: int
    maxLoseCount: int
    state: str
    isPromo: bool
    isUdemaeUp: bool
    udemaeAfter: str
    earnedUdemaePoint: int


@dataclass(repr=False)
class anarchyHistoryGroupsNodesSchema(JSONDataClass):
    bankaraMatchChallenge: bankaraMatchChallengeSchema
    historyDetails: anarchyHistoryDetailsSchema


@dataclass(repr=False)
class regularHistoryGroupsNodesSchema(JSONDataClass):
    historyDetails: regularHistoryDetailsSchema


@dataclass(repr=False)
class anarchyHistoryGroupsSchema(JSONDataClass):
    nodes: list[anarchyHistoryGroupsNodesSchema]


@dataclass(repr=False)
class regularHistoryGroupsSchema(JSONDataClass):
    nodes: list[regularHistoryGroupsNodesSchema]
