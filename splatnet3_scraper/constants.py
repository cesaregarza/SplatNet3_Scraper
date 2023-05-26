SPLATNET_URL = "https://api.lp1.av5ja.srv.nintendo.net"
GRAPHQL_URL = SPLATNET_URL + "/api/graphql"
GRAPH_QL_REFERENCE_URL = (
    "https://raw.githubusercontent.com"
    "/imink-app/SplatNet3/master/Data/splatnet3_webview_data.json"
)
IOS_APP_URL = (
    "https://apps.apple.com/us/app/nintendo-switch-online/id1234806557"
)
IMINK_URL = "https://api.imink.app/f"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
    + "AppleWebKit/537.36 (KHTML, like Gecko) "
    + "Chrome/94.0.4606.61 "
    + "Mobile Safari/537.36"
)
WEB_VIEW_VERSION_FALLBACK = "3.0.0-0742bda0"
APP_VERSION_FALLBACK = "2.5.1"
HASHES_FALLBACK = {
    "BankaraBattleHistoriesQuery": "0438ea6978ae8bd77c5d1250f4f84803",
    "BankaraBattleHistoriesRefetchQuery": "92b56403c0d9b1e63566ec98fef52eb3",
    "BattleHistoryCurrentPlayerQuery": "49dd00428fb8e9b4dde62f585c8de1e0",
    "CatalogQuery": "ff12098bad4989a813201b00ff22ac4e",
    "CatalogRefetchQuery": "60a6592c6ee8e47245020ae0d314d378",
    "ChallengeQuery": "8a079214500148bf88a8fce1d7209b90",
    "ChallengeRefetchQuery": "34aedc79f96b8613501bba465295f779",
    "CheckinQuery": "5d0d1b45ebf4e324d0dae017d9df06d2",
    "CheckinWithQRCodeMutation": "daffd9621680664dbf19d27e87484ac7",
    "ConfigureAnalyticsQuery": "f8ae00773cc412a50dd41a6d9a159ddd",
    "CoopHistoryDetailQuery": "379f0d9b78b531be53044bcac031b34b",
    "CoopHistoryDetailRefetchQuery": "d3188df2fd4436870936b109675e2849",
    "CoopHistoryQuery": "91b917becd2fa415890f5b47e15ffb15",
    "CoopPagerLatestCoopQuery": "eb947416660e0a7520549f6b9a8ffcd7",
    "CoopRecordBigRunRecordContainerPaginationQuery": (
        "2b83817b6e88b202d25939fe04658d33"
    ),
    "CoopRecordQuery": "b2f05c682ed2aeb669a86a3265ceb713",
    "CoopRecordRefetchQuery": "15035e6c4308b32d1a77e87398be5cd4",
    "CreateMyOutfitMutation": "31ff008ea218ffbe11d958a52c6f959f",
    "DetailFestRecordDetailQuery": "96c3a7fd484b8d3be08e0a3c99eb2a3d",
    "DetailFestRefethQuery": "18c7c465b18de5829347b7a7f1e571a1",
    "DetailFestVotingStatusRefethQuery": "92f51ed1ab462bbf1ab64cad49d36f79",
    "DetailRankingQuery": "cc38f388c51f9930bd7cca966893f1b4",
    "DetailTabViewWeaponTopsArRefetchQuery": "a6782a0c692e8076656f9b4ab613fd82",
    "DetailTabViewWeaponTopsClRefetchQuery": "8d3c5bb2e82d6eb32a37eefb0e1f8f69",
    "DetailTabViewWeaponTopsGlRefetchQuery": "b23468857c049c2f0684797e45fabac1",
    "DetailTabViewWeaponTopsLfRefetchQuery": "d46f88c2ea5c4daeb5fe9d5813d07a99",
    "DetailTabViewXRankingArRefetchQuery": "6de3895bd90b5fa5220b5e9355981e16",
    "DetailTabViewXRankingClRefetchQuery": "3ab25d7f475cb3d5daf16f835a23411b",
    "DetailTabViewXRankingGlRefetchQuery": "d62ec65b297968b659103d8dc95d014d",
    "DetailTabViewXRankingLfRefetchQuery": "d96057b8f46e5f7f213a35c8ea2b8fdc",
    "DetailVotingStatusQuery": "53ee6b6e2acc3859bf42454266d671fc",
    "DownloadSearchReplayQuery": "8e904b52b5080b6f4b4448a50762362c",
    "FestRecordQuery": "44c76790b68ca0f3da87f2a3452de986",
    "FestRecordRefetchQuery": "73b9837d0e4dd29bfa2f1a7d7ee0814a",
    "FriendListQuery": "f0a8ebc384cf5fbac01e8085fbd7c898",
    "FriendListRefetchQuery": "aa2c979ad21a1100170ddf6afea3e2db",
    "GesotownQuery": "a43dd44899a09013bcfd29b4b13314ff",
    "GesotownRefetchQuery": "951cab295eafdbeccfc2e718d7a98646",
    "HeroHistoryQuery": "fbee1a882371d4e3becec345636d7d1c",
    "HeroHistoryRefetchQuery": "4f9ae2b8f1d209a5f20302111b28f975",
    "HistoryRecordQuery": "f09da9d24d888797fdfb2f060dbdf4ed",
    "HistoryRecordRefetchQuery": "d997d8e3875d50d3a1dc7e8a756e9e07",
    "HomeQuery": "22e2fa8294168003c21b00c333c35384",
    "JourneyChallengeDetailQuery": "5a199948d059985bd758cc0175131f4a",
    "JourneyChallengeDetailRefetchQuery": "e7414c7a64bf80bb50ce21d5ccfde772",
    "JourneyQuery": "bc71fc0264f3f72256724b069f7a4097",
    "JourneyRefetchQuery": "09eee118fa16415d6bc3846bc6e5d8e5",
    "LatestBattleHistoriesQuery": "0176a47218d830ee447e10af4a287b3f",
    "LatestBattleHistoriesRefetchQuery": "7161210aad0793e58e76f20e0443855e",
    "MyOutfitDetailQuery": "d935d9e9ba7a5b6b5d6ece7f253304fc",
    "MyOutfitsQuery": "81d9a6849467d2aa6b1603ebcedbddbe",
    "MyOutfitsRefetchQuery": "10db4e349f3123c56df14e3adec2ee6f",
    "PagerLatestVsDetailQuery": "0329c535a32f914fd44251be1f489e24",
    "PagerUpdateBattleHistoriesByVsModeQuery": (
        "094a9b44ff21e8c409d6046fc1af9dfe"
    ),
    "PhotoAlbumQuery": "7e950e4f69a5f50013bba8a8fb6a3807",
    "PhotoAlbumRefetchQuery": "53fb0ad32c13dd9a6e617b1158cc2d41",
    "PrivateBattleHistoriesQuery": "8e5ae78b194264a6c230e262d069bd28",
    "PrivateBattleHistoriesRefetchQuery": "89bc61012dcf170d9253f406ebebee67",
    "RankingHoldersFestTeamRankingHoldersPaginationQuery": (
        "f488fccdad37b9e19aed50a8d6e83a24"
    ),
    "RegularBattleHistoriesQuery": "3baef04b095ad8975ea679d722bc17de",
    "RegularBattleHistoriesRefetchQuery": "4c95233c8d55e7c8cc23aae06109a2e8",
    "ReplayModalReserveReplayDownloadMutation": (
        "87bff2b854168b496c2da8c0e7f3e5bc"
    ),
    "ReplayQuery": "e9cbaa835977b6c6de77ca7a4be15b24",
    "ReplayUploadedReplayListRefetchQuery": "3bd200163e63bfff42ab60a244cac042",
    "SaleGearDetailOrderGesotownGearMutation": (
        "b79b7a101a243912754f72437e2ad7e5"
    ),
    "SaleGearDetailQuery": "6eb1b255b2cf04c08041567148c883ad",
    "SettingQuery": "73bd677ed986ad2cb7004ceabfff4d38",
    "StageRecordQuery": "f08a932d533845dde86e674e03bbb7d3",
    "StageRecordsRefetchQuery": "2fb1b3fa2d40c9b5953ea1ae263e54c1",
    "StageScheduleQuery": "011e394c0e384d77a0701474c8c11a20",
    "SupportButton_SupportChallengeMutation": (
        "991bace9e8c52d63084cd1570a97a5b4"
    ),
    "UpdateMyOutfitMutation": "bb809066282e7d659d3b9e9d4e46b43b",
    "VotesUpdateFestVoteMutation": "a2c742c840718f37488e0394cd6e1e08",
    "VsHistoryDetailPagerRefetchQuery": "994cf141e55213e6923426caf37a1934",
    "VsHistoryDetailQuery": "291295ad311b99a6288fc95a5c4cb2d2",
    "WeaponRecordQuery": "5f279779e7081f2d14ae1ddca0db2b6e",
    "WeaponRecordsRefetchQuery": "6961f618fcef440c81509b205465eeec",
    "XBattleHistoriesQuery": "6796e3cd5dc3ebd51864dc709d899fc5",
    "XBattleHistoriesRefetchQuery": "94711fc9f95dd78fc640909f02d09215",
    "XRankingDetailQuery": "d5e4924c05891208466fcba260d682e7",
    "XRankingDetailRefetchQuery": "fb960404299958248b3c0a2fbb444c35",
    "XRankingQuery": "d771444f2584d938db8d10055599011d",
    "XRankingRefetchQuery": "5149402597bd2531b4eea04692d8bfd5",
    "myOutfitCommonDataEquipmentsQuery": "d29cd0c2b5e6bac90dd5b817914832f8",
    "myOutfitCommonDataFilteringConditionQuery": (
        "d02ab22c9dccc440076055c8baa0fa7a"
    ),
    "refetchableCoopHistory_coopResultQuery": (
        "50be9b694c7c6b99b7a383e494ec5258"
    ),
    "useCurrentFestQuery": "c0429fd738d829445e994d3370999764",
    "useShareMyOutfitQuery": "3ba5572efce5bebbd859fc2d269d223c",
}


class TOKENS:
    SESSION_TOKEN = "session_token"
    GTOKEN = "gtoken"
    BULLET_TOKEN = "bullet_token"


TOKEN_EXPIRATIONS = {
    TOKENS.GTOKEN: (60 * 60 * 6) + (60 * 30),
    TOKENS.BULLET_TOKEN: (60 * 60 * 2),
}
ENV_VAR_NAMES = {
    TOKENS.SESSION_TOKEN: "SN3S_SESSION_TOKEN",
    TOKENS.GTOKEN: "SN3S_GTOKEN",
    TOKENS.BULLET_TOKEN: "SN3S_BULLET_TOKEN",
}

PRIMARY_ONLY = [
    "Comeback",
    "Last-Ditch Effort",
    "Opening Gambit",
    "Tenacity",
    "Ability Doubler",
    "Haunt",
    "Ninja Squid",
    "Respawn Punisher",
    "Thermal Ink",
    "Drop Roller",
    "Object Shredder",
    "Stealth Jump",
]

ABILITIES = [
    "Ink Saver (Main)",
    "Ink Saver (Sub)",
    "Ink Recovery Up",
    "Run Speed Up",
    "Swim Speed Up",
    "Special Charge Up",
    "Special Saver",
    "Special Power Up",
    "Quick Respawn",
    "Quick Super Jump",
    "Sub Power Up",
    "Ink Resistance Up",
    "Sub Resistance Up",
    "Intensify Action",
]

ALL_ABILITIES = PRIMARY_ONLY + ABILITIES
