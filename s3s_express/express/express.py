from s3s_express.base.graph_ql_queries import GraphQLQueries, queries
from s3s_express.base.tokens import NSO, TokenManager
from s3s_express.express.config import Config


class S3S_Express:
    """This class implements all of the classes and functions defined in the
    s3s_express.base module and can be seen as an example of how to put them
    together. While the class has a method to create the session token, a full
    implementation with a CLI is outside the scope of this project.
    """

    def __init__(self, config: Config) -> None:
        """Initializes the class, it is not meant to be instantiated directly,
        but rather through one of the available factory methods.
        """
        self.config = config

    @staticmethod
    def from_config_file(config_file: str | None = None) -> "S3S_Express":
        """Creates a new instance of the class using a configuration file. If
        no configuration file is provided, the default configuration file,
        .s3s_express, will be used.

        Args:
            config_file (str | None): The path to the configuration file. If
                None, the default configuration file will be used. Defaults to
                None.

        Returns:
            S3S_Express: A new instance of the class.
        """
        config = Config(config_file)
        return S3S_Express(config)

    @staticmethod
    def generate_session_token_url(
        user_agent: str | None = None,
    ) -> tuple[str, bytes, bytes]:
        """Generates the URL to use to get the session token.

        Args:
            user_agent (str | None): The user agent to use. If None, the default
                user agent will be used. Defaults to None.

        Returns:
            tuple:
                str: The URL to use to get the session token.
                bytes: The session ID
                bytes: The challenge solution
        """
        nso = NSO.new_instance()
        return nso.generate_login_url(user_agent)

    @staticmethod
    def from_session_token(session_token: str) -> "S3S_Express":
        """Creates a new instance of the class using a session token.

        Args:
            session_token (str): The session token.

        Returns:
            S3S_Express: A new instance of the class.
        """
        token_manager = TokenManager.from_session_token(session_token)
