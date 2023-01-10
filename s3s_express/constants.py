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
WEB_VIEW_VERSION_FALLBACK = "2.0.0-bd36a652"


class TOKENS:
    SESSION_TOKEN = "session_token"
    GTOKEN = "gtoken"
    BULLET_TOKEN = "bullet_token"


TOKEN_EXPIRATIONS = {
    TOKENS.GTOKEN: (60 * 60 * 6) + (60 * 30),
    TOKENS.BULLET_TOKEN: (60 * 60 * 2),
}
ENV_VAR_NAMES = {
    TOKENS.SESSION_TOKEN: "S3S_SESSION_TOKEN",
    TOKENS.GTOKEN: "S3S_GTOKEN",
    TOKENS.BULLET_TOKEN: "S3S_BULLET_TOKEN",
}
