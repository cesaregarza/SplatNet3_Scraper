SPLATNET_URL = "https://api.lp1.av5ja.srv.nintendo.net"
GRAPHQL_URL = SPLATNET_URL + "/api/graphql"
GRAPH_QL_REFERENCE_URL = (
    "https://raw.githubusercontent.com"
    "/imink-app/SplatNet3/master/Data/splatnet3_webview_data.json"
)
IOS_APP_URL = (
    "https://apps.apple.com/us/app/nintendo-switch-online/id1234806557"
)
NXAPI_ZNCA_URL = "https://nxapi-znca-api.fancy.org.uk/api/znca/f"
NXAPI_ENCRYPT_URL = (
    "https://nxapi-znca-api.fancy.org.uk/api/znca/encrypt-request"
)
NXAPI_DECRYPT_URL = (
    "https://nxapi-znca-api.fancy.org.uk/api/znca/decrypt-response"
)
NXAPI_CONFIG_URL = "https://nxapi-znca-api.fancy.org.uk/api/znca/config"
NXAPI_CONFIG_URL_ENV = "NXAPI_CONFIG_URL"
NXAPI_CONFIG_CACHE_TTL = 3600  # Cache config for 1 hour
# Scopes: ca:gf=generate-f, ca:er=encrypt-request, ca:dr=decrypt-response
NXAPI_DEFAULT_AUTH_SCOPE = "ca:gf ca:er ca:dr"
NXAPI_CLIENT_ID_ENV = "NXAPI_ZNCA_API_CLIENT_ID"
NXAPI_CLIENT_SECRET_ENV = "NXAPI_ZNCA_API_CLIENT_SECRET"
NXAPI_CLIENT_SECRET_ENV_ALIASES = (
    "NXAPI_ZNCA_API_SHARED_SECRET",
    "NXAPI_SHARED_SECRET",
)
NXAPI_CLIENT_ASSERTION_ENV = "NXAPI_ZNCA_API_CLIENT_ASSERTION"
NXAPI_CLIENT_ASSERTION_TYPE_ENV = "NXAPI_ZNCA_API_CLIENT_ASSERTION_TYPE"
NXAPI_CLIENT_ASSERTION_PRIVATE_KEY_PATH_ENV = (
    "NXAPI_ZNCA_API_CLIENT_ASSERTION_PRIVATE_KEY_PATH"
)
NXAPI_CLIENT_ASSERTION_JKU_ENV = "NXAPI_ZNCA_API_CLIENT_ASSERTION_JKU"
NXAPI_CLIENT_ASSERTION_KID_ENV = "NXAPI_ZNCA_API_CLIENT_ASSERTION_KID"
NXAPI_SCOPE_ENV = "NXAPI_ZNCA_API_AUTH_SCOPE"
NXAPI_USER_AGENT_ENV = "NXAPI_USER_AGENT"
NXAPI_CLIENT_VERSION_ENV = "NXAPI_ZNCA_API_CLIENT_VERSION"
NXAPI_AUTH_TOKEN_URL = "https://nxapi-auth.fancy.org.uk/api/oauth/token"
NXAPI_AUTH_TOKEN_URL_ENV = "NXAPI_AUTH_TOKEN_URL"
NXAPI_DEFAULT_CLIENT_VERSION = "hio87-mJks_e9GNF"
CORAL_API_URL = "https://api-lp1.znc.srv.nintendo.net"
CORAL_ACCOUNT_LOGIN_PATH = "/v4/Account/Login"
CORAL_GET_WEB_SERVICE_TOKEN_PATH = "/v4/Game/GetWebServiceToken"
ZNCA_PLATFORM_VERSION = "12"
APP_ID_TOKEN_LIFETIME = 15 * 60
WEB_SERVICE_ID_TOKEN_LIFETIME = 2 * 60 * 60
AUTH_FAILURE_COOLDOWN = 10
RATE_LIMIT_BASE_COOLDOWN = 30
RATE_LIMIT_COOLDOWN_CAP = 5 * 60
DEFAULT_F_TOKEN_URL = [NXAPI_ZNCA_URL]
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 12; Pixel 7a) "
    + "AppleWebKit/537.36 (KHTML, like Gecko) "
    + "Chrome/120.0.6099.230 "
    + "Mobile Safari/537.36"
)
APP_VERSION_FALLBACK = "3.1.0"
APP_VERSION_OVERRIDE_ENV = "SPLATNET3_APP_VERSION"


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
