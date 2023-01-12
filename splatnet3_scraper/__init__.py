import pathlib
import re

# Read version number from TOML
self_path = pathlib.Path(__file__).parent.parent
toml_path = self_path / "pyproject.toml"
with open(toml_path, "rb") as f:
    lines = f.readlines()
version_line = [str(line) for line in lines if "version" in str(line)][0]
version = re.search(r"\d+\.\d+\.\d+", version_line).group(0)
__version__ = version

from splatnet3_scraper.scraper import SplatNet3_Scraper
