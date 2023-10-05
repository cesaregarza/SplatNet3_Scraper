class QueryMap:
    BANKARA_BATTLE_HISTORIES = "BankaraBattleHistoriesQuery"
    BANKARA_BATTLE_HISTORIES_REFETCH = "BankaraBattleHistoriesRefetchQuery"
    BATTLE_HISTORY_CURRENT_PLAYER = "BattleHistoryCurrentPlayerQuery"
    CATALOG = "CatalogQuery"
    CHECKIN = "CheckinQuery"
    CHECKIN_QR = "CheckinWithQRCodeMutation"
    CONFIGURE_ANALYTICS = "ConfigureAnalyticsQuery"
    COOP_HISTORY_DETAIL = "CoopHistoryDetailQuery"
    COOP_HISTORY_DETAIL_REFETCH = "CoopHistoryDetailRefetchQuery"
    COOP_HISTORY = "CoopHistoryQuery"
    COOP_PAGER_LATEST_COOP = "CoopPagerLatestCoopQuery"
    COOP_RECORD_BIG_RUN_RECORD_CONTAINER_PAGINATION = (
        "CoopRecordBigRunRecordContainerPaginationQuery"
    )
    COOP_RECORD = "CoopRecordQuery"
    COOP_RECORD_REFETCH = "CoopRecordRefetchQuery"
    CREATE_MY_OUTFIT_MUTATION = "CreateMyOutfitMutation"
    DETAIL_FEST_RECORD_DETAIL = "DetailFestRecordDetailQuery"
    DETAIL_FEST_REFETCH = "DetailFestRefethQuery"
    DETAIL_FEST_VOTING_STATUS_REFETCH = "DetailFestVotingStatusRefethQuery"
    DETAIL_RANKING = "DetailRankingQuery"
    DETAIL_TAB_VIEW_WEAPON_TOPS_AR_REFETCH = (
        "DetailTabViewWeaponTopsArRefetchQuery"
    )
    DETAIL_TAB_VIEW_WEAPON_TOPS_CL_REFETCH = (
        "DetailTabViewWeaponTopsClRefetchQuery"
    )
    DETAIL_TAB_VIEW_WEAPON_TOPS_GL_REFETCH = (
        "DetailTabViewWeaponTopsGlRefetchQuery"
    )
    DETAIL_TAB_VIEW_WEAPON_TOPS_LF_REFETCH = (
        "DetailTabViewWeaponTopsLFRefetchQuery"
    )
    DETAIL_TAB_VIEW_X_RANKING_AR_REFETCH = "DetailTabViewXRankingArRefetchQuery"
    DETAIL_TAB_VIEW_X_RANKING_CL_REFETCH = "DetailTabViewXRankingClRefetchQuery"
    DETAIL_TAB_VIEW_X_RANKING_GL_REFETCH = "DetailTabViewXRankingGlRefetchQuery"
    DETAIL_TAB_VIEW_X_RANKING_LF_REFETCH = "DetailTabViewXRankingLFRefetchQuery"
    DETAIL_VOTING_STATUS = "DetailVotingStatusQuery"
    DOWNLOAD_SEARCH_REPLAY = "DownloadSearchReplayQuery"
    FEST_RECORD = "FestRecordQuery"
    FEST_RECORD_REFETCH = "FestRecordRefetchQuery"
    FRIEND_LIST = "FriendListQuery"
    FRIEND_LIST_REFETCH = "FriendListRefetchQuery"
    GESOTOWN = "GesotownQuery"
    GESOTOWN_REFETCH = "GesotownRefetchQuery"
    HERO_HISTORY = "HeroHistoryQuery"
    HERO_HISTORY_REFETCH = "HeroHistoryRefetchQuery"
    HISTORY_RECORD = "HistoryRecordQuery"
    HISTORY_RECORD_REFETCH = "HistoryRecordRefetchQuery"
    HOME = "HomeQuery"
    JOURNEY_CHALLENGE_DETAIL = "JourneyChallengeDetailQuery"
    JOURNEY_CHALLENGE_DETAIL_REFETCH = "JourneyChallengeDetailRefetchQuery"
    JOURNEY = "JourneyQuery"
    JOURNEY_REFETCH = "JourneyRefetchQuery"
    LATEST_BATTLE_HISTORIES = "LatestBattleHistoriesQuery"
    LATEST_BATTLE_HISTORIES_REFETCH = "LatestBattleHistoriesRefetchQuery"
    MY_OUTFITS_DETAIL = "MyOutfitsDetailQuery"
    MY_OUTFITS = "MyOutfitsQuery"
    MY_OUTFITS_REFETCH = "MyOutfitsRefetchQuery"
    PAGER_LATEST_VS_DETAIL = "PagerLatestVsDetailQuery"
    PAGER_UPDATE_BATTLE_HISTORIES_BY_VS_MODE = (
        "PagerUpdateBattleHistoriesByVsModeQuery"
    )
    PHOTO_ALBUM = "PhotoAlbumQuery"
    PHOTO_ALBUM_REFETCH = "PhotoAlbumRefetchQuery"
    PRIVATE_BATTLE_HISTORIES = "PrivateBattleHistoriesQuery"
    PRIVATE_BATTLE_HISTORIES_REFETCH = "PrivateBattleHistoriesRefetchQuery"
    RANKING_HOLDERS_FEST_TEAM_RANKING_HOLDERS_PAGINATION = (
        "RankingHoldersFestTeamRankingHoldersPaginationQuery"
    )
    REGULAR_BATTLE_HISTORIES = "RegularBattleHistoriesQuery"
    REGULAR_BATTLE_HISTORIES_REFETCH = "RegularBattleHistoriesRefetchQuery"
    REPLAY_MODAL_RESERVE_REPLAY_DOWNLOAD_MUTATION = (
        "ReplayModalReserveReplayDownloadMutation"
    )
    REPLAY = "ReplayQuery"
    REPLAY_UPLOADED_REPLAY_LIST_REFETCH = "ReplayUploadedReplayListRefetchQuery"
    SALE_GEAR_DETAIL_ORDER_GESOTOWN_GEAR_MUTATION = (
        "SaleGearDetailOrderGesotownGearMutation"
    )
    SALE_GEAR_DETAIL = "SaleGearDetailQuery"
    SETTING = "SettingQuery"
    STAGE_RECORD = "StageRecordQuery"
    STAGE_RECORDS_REFETCH = "StageRecordsRefetchQuery"
    STAGE_SCHEDULE = "StageScheduleQuery"
    SUPPORT_BUTTON_SUPPORT_CHALLENGE_MUTATION = (
        "SupportButton_SupportChallengeMutation"
    )
    UPDATE_MY_OUTFIT_MUTATION = "UpdateMyOutfitMutation"
    VOTES_UPDATE_FEST_VOTE_MUTATION = "VotesUpdateFestVoteMutation"
    VS_HISTORY_DETAIL_PAGER_REFETCH = "VsHistoryDetailPagerRefetchQuery"
    VS_HISTORY_DETAIL = "VsHistoryDetailQuery"
    WEAPON_RECORD = "WeaponRecordQuery"
    WEAPON_RECORDS_REFETCH = "WeaponRecordsRefetchQuery"
    X_BATTLE_HISTORIES = "XBattleHistoriesQuery"
    X_BATTLE_HISTORIES_REFETCH = "XBattleHistoriesRefetchQuery"
    X_RANKING_DETAIL = "XRankingDetailQuery"
    X_RANKING_DETAIL_REFETCH = "XRankingDetailRefetchQuery"
    X_RANKING = "XRankingQuery"
    X_RANKING_REFETCH = "XRankingRefetchQuery"
    MY_OUTFIT_COMMON_DATA_EQUIPMENTS = "myOutfitCommonDataEquipmentsQuery"
    MY_OUTFIT_COMMON_DATA_FILTERING_CONDITION = (
        "myOutfitCommonDataFilteringConditionQuery"
    )
    REFETCHABLE_COOP_HISTORY_COOP_RESULT = (
        "refetchableCoopHistory_coopResultQuery"
    )
    USE_CURRENT_FEST = "useCurrentFestQuery"

    # Convenience aliases
    VS_DETAIL = "VsHistoryDetailQuery"
    SALMON_DETAIL = "CoopHistoryDetailQuery"
    ANARCHY = "BankaraBattleHistoriesQuery"
    REGULAR = "RegularBattleHistoriesQuery"
    XBATTLE = "XBattleHistoriesQuery"
    PRIVATE = "PrivateBattleHistoriesQuery"
    LATEST = "LatestBattleHistoriesQuery"
    SALMON = "CoopHistoryQuery"
    SALMON_RUN = "CoopHistoryQuery"
    TURF = "RegularBattleHistoriesQuery"
    COOP = "CoopHistoryQuery"
    CHALLENGE = "EventBattleHistoriesQuery"
    EVENT = "EventBattleHistoriesQuery"
    ANARCHY_DETAIL = "VsHistoryDetailQuery"
    TURF_DETAIL = "VsHistoryDetailQuery"
    REGULAR_DETAIL = "VsHistoryDetailQuery"
    X_DETAIL = "VsHistoryDetailQuery"
    XBATTLE_DETAIL = "VsHistoryDetailQuery"
    PRIVATE_DETAIL = "VsHistoryDetailQuery"
    LATEST_DETAIL = "VsHistoryDetailQuery"
    COOP_DETAIL = "CoopHistoryDetailQuery"
    SALMON_DETAIL = "CoopHistoryDetailQuery"
    CHALLENGE_DETAIL = "VsHistoryDetailQuery"

    @staticmethod
    def get(query: str) -> str:
        """Gets the query from the query map.

        Args:
            query (str): The query to get.

        Returns:
            str: The query.
        """
        return getattr(QueryMap, query.upper())
