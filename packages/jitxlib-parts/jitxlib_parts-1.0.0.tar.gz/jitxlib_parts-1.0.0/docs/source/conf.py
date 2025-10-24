# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Add jitx source to import path
import sys
from pathlib import Path
from sphinx.ext import autodoc

sys.path.insert(0, str(Path("..", "..", "src").resolve()))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "jitx-parts"
copyright = "2025, JITX Inc"  # noqa: A001
author = "JITX Inc"
version = "0.1"
release = "0.1.0dev1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

needs_sphinx = "8.1"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
]
templates_path = ["_templates"]
exclude_patterns = []

# -- Autodoc configuration --------------------------------------------------
# Include both class and __init__ docstrings
autoclass_content = "both"
# Include private members (starting with _) if they have docstrings
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "special-members": "__init__",
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


html_theme = "pydata_sphinx_theme"
html_theme_options = {
    # "announcement": "This is an annoucement",
    "show_version_warning_banner": True,
    # "content_footer_items": ["last-updated"],
    "show_nav_level": 1,
    "navigation_depth": 6,
    "show_toc_level": 4,  # right sidebar
    "collapse_navigation": False,
    "sidebar_includehidden": True,
    "navbar_start": ["navbar-logo", "version-switcher"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    # "navbar_persistent": ["search-button"],
    "navbar_align": "right",
    "footer_start": ["copyright"],
    "footer_end": ["last-updated"],
    "secondary_sidebar_items": ["page-toc", "sourcelink"],
    "show_prev_next": False,
    "check_switcher": False,
    "switcher": {
        "json_url": "/_static/versions.json",
        "version_match": version,
    },
    "external_links": [
        {"name": "JITX", "url": "https://jitx.com/"},
        {
            "name": "Download",
            "url": "https://marketplace.visualstudio.com/items?itemName=JITX.jitpcb-vscode",
        },
    ],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/JITX-Inc",
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
        },
    ],
}
html_show_sourcelink = True
html_static_path = ["_static"]

# -- Don't show "Bases: object" in api docs ----------------------------------
# https://stackoverflow.com/questions/46279030/how-can-i-prevent-sphinx-from-listing-object-as-a-base-class


class MockedClassDocumenter(autodoc.ClassDocumenter):
    def add_line(self, line: str, source: str, *lineno: int) -> None:
        if line == "   Bases: :py:class:`object`":
            return
        super().add_line(line, source, *lineno)


autodoc.ClassDocumenter = MockedClassDocumenter
