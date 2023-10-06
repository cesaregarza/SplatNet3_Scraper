# This does not test the actual functionality of the code. Anything that needs
# some sort of assurance before pushing to production should be tested here.
import re
import pytest

import splatnet3_scraper

@pytest.mark.production
def test_version():
    # Make sure the version in the toml file matches the version in the code.
    with open("pyproject.toml") as f:
        lines = f.readlines()

    version_line = [str(line) for line in lines if "version" in str(line)][0]
    version = re.search(r"\d+\.\d+\.\d+", version_line).group(0)
    assert version == splatnet3_scraper.__version__


def test_slushie():
    # This test exists to satisfy Slushie's need for a nice round 400 tests
    # rather than 399.
    assert True
