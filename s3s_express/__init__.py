import pathlib

import tomli

from s3s_express.logs import Logger

logger = Logger("s3s_express.log")

# Read version number from TOML
self_path = pathlib.Path(__file__).parent.parent
toml_path = self_path / "pyproject.toml"
with open(toml_path, "rb") as f:
    toml = tomli.load(f)
version = toml["tool"]["poetry"]["version"]
__version__ = version
