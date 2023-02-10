# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import pathlib
import sys
sys.path.insert(0, pathlib.Path(__file__).parents[2].resolve().as_posix())
import splatnet3_scraper

project = "SplatNet 3 Scraper"
copyright = "2023, Cesar Eduardo Garza"
author = "Cesar Eduardo Garza"
release = splatnet3_scraper.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration



extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_immaterial",
    "sphinx_immaterial.apidoc.python.apigen",
]

templates_path = ["_templates"]
exclude_patterns = []

python_apigen_modules = {
    "splatnet3_scraper": "generated/main/",
    "splatnet3_scraper.scraper": "generated/scraper/",
    "splatnet3_scraper.query": "generated/query/",
    "splatnet3_scraper.auth": "generated/auth/",
}

python_apigen_default_groups = [
    ("class:.*", "Classes"),
    ("data:.*", "Variables"),
    ("function:.*", "Functions"),
    ("classmethod:.*", "Class methods"),
    ("method:.*", "Methods"),
    (r"method:.*\.[A-Z][A-Za-z,_]*", "Constructors"),
    (r"method:.*\.__[A-Za-z,_]*__", "Special methods"),
    (r"method:.*\.__(init|new)__", "Constructors"),
    (r"method:.*\.__(str|repr)__", "String representation"),
    ("property:.*", "Properties"),
    (r".*:.*\.is_[a-z,_]*", "Attributes"),
]
python_apigen_default_order = [
    ("class:.*", 10),
    ("data:.*", 11),
    ("function:.*", 12),
    ("classmethod:.*", 40),
    ("method:.*", 50),
    (r"method:.*\.[A-Z][A-Za-z,_]*", 20),
    (r"method:.*\.__[A-Za-z,_]*__", 28),
    (r"method:.*\.__(init|new)__", 20),
    (r"method:.*\.__(str|repr)__", 30),
    ("property:.*", 60),
    (r".*:.*\.is_[a-z,_]*", 70),
]
python_apigen_order_tiebreaker = "alphabetical"
python_apigen_case_insensitive_filesystem = False
python_apigen_show_base_classes = True

napoleon_custom_sections = [("Returns", "params_style")]

html_theme_options = {
    "repo_url": "https://github.com/cesaregarza/SplatNet3_Scraper",
    "repo_name": "cesaregarza/SplatNet3_Scraper",
    "repo_type": "github",
    "social": [
        {
            "icon": "fontawesome/brands/github",
            "link": "https://github.com/cesaregarza/SplatNet3_Scraper",
        }
    ],
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_immaterial"
html_static_path = ["_static"]

# Other options
autodoc_typehints = "description"
