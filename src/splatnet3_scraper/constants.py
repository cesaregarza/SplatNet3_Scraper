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
ZNCA_URL = "https://nxapi-znca-api.fancy.org.uk/api/znca/f"
DEFAULT_F_TOKEN_URL = [IMINK_URL, ZNCA_URL]
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
    + "AppleWebKit/537.36 (KHTML, like Gecko) "
    + "Chrome/94.0.4606.61 "
    + "Mobile Safari/537.36"
)
APP_VERSION_FALLBACK = "2.7.0"


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
