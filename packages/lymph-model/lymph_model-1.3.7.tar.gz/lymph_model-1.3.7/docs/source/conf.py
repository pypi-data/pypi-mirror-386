# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/main/usage/configuration.html
import lymph

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "lymph"
copyright = "2022, Roman Ludwig"
author = "Roman Ludwig"
gh_username = "rmnldwg"

version = lymph.__version__
# The full version, including alpha/beta/rc tags
release = lymph.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "myst_nb",
]

# MyST settings
myst_enable_extensions = ["colon_fence", "dollarmath"]
nb_execution_mode = "auto"
nb_execution_timeout = 120

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_data"]

# document classes and their constructors
autoclass_content = "class"

# sort members by source
autodoc_member_order = "bysource"

# show type hints
autodoc_typehints = "signature"


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

html_theme = "sphinx_book_theme"
html_theme_options = {
    "repository_url": f"https://github.com/{gh_username}/{project}",
    "repository_branch": "main",
    "use_repository_button": True,
}

# import sphinx_modern_theme
# html_theme = "sphinx_modern_theme"
# html_theme_path = [sphinx_modern_theme.get_html_theme_path()]

# html_theme = "bootstrap-astropy"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["./_static"]
html_css_files = [
    "css/custom.css",
]
