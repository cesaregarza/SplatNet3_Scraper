from s3s_express.base.graph_ql_queries import GraphQLQueries, queries
from s3s_express.base.tokens import TokenManager
from s3s_express.express.config import Config


class S3S_Express:
    """This class implements all of the classes and functions defined in the
    s3s_express.base module and can be seen as an example of how to put them
    together.
    """

    def __init__(self, config: Config, token_manager: TokenManager) -> None:
        """Initializes the class, it is not meant to be instantiated directly,
        but rather through one of the available factory methods.
        """
        self.config = config
        self.token_manager = token_manager

    @staticmethod
    def from_config_file(config_file: str) -> "S3S_Express":
        """Creates a new instance of the class using a configuration file.

        Args:
            config_file (str): The path to the configuration file.

        Returns:
            S3S_Express: A new instance of the class.
        """
        config = Config()
        token_manager = TokenManager.from_config_file(config_file)
        return S3S_Express(config, token_manager)
