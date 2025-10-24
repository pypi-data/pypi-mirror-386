import os
import sys
import tomllib

sys.path.insert(0, os.path.abspath("."))


# Project Details
with open("../../pyproject.toml", "rb") as f:
    config = tomllib.load(f)

project = config["project"]["name"]
copyright = config["project"]["license"]["text"]
author = config["project"]["authors"][0]["name"]
release = config["project"]["version"]


# Extensions
extensions = [
    "breathe",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
    "sphinx_math_dollar",
    "sphinx.ext.napoleon",  # for Google/NumPy docstrings
    "sphinx.ext.mathjax",   # for Latex math mode
    "myst_parser",          # for Markdown support
]
breathe_projects = {"SHiP": "../doxygen/xml"}
breathe_default_project = "SHiP"
breathe_default_members = ("members",)
autodoc_typehints = "description"
# autosectionlabel_prefix_document = False
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "member-order": "groupwise",
    "special-members": "__init__",
    # "no-module": True,
}
myst_enable_extensions = [
    "amsmath",     # optional, enables AMS math environments
    "dollarmath",  # enables $...$ and $$...$$
]


html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,  # keeps navigation expanded by default
    "sticky_navigation": True,     # sidebar sticks on scroll
    "navigation_depth": 7,         # how deep ToC shows
}
html_static_path = ["_static"]


# conf.py
def fix_verbatim_breaks(app, exception):
    if not exception:
        for f in app.outdir.rglob("*.html"):
            html = f.read_text()
            f.write_text(html.replace('. </p>\n<p><span> <a class="reference internal" ', '<span> <a class="reference internal" '))


def setup(app):
    app.add_css_file("custom.css")
    app.connect("build-finished", fix_verbatim_breaks)
