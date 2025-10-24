from __future__ import annotations

import os
import sys
from pprint import pformat

import spark3dbatch
import sphinx
from sphinx.util import inspect

# Add the _ext/ folder so that Sphinx can find it
sys.path.append(os.path.abspath("./_ext"))

project = "Spark3DBatch"
author = "A. Plaçais, J. Hillairet"
copyright = "2025, " + author

# See https://protips.readthedocs.io/git-tag-version.html
# The full version, including alpha/beta/rc tags.
# release = re.sub("^v", "", os.popen("git describe").read().strip())
# The short X.Y version.
# version = release
version = spark3dbatch.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_extensions",
    "myst_parser",
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx_rtd_theme",
    "sphinx_tabs.tabs",
    # "sphinxcontrib.bibtex",
]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",  # Keep original members order
    "private-members": True,  # Document _private members
    "special-members": "__init__, __post_init__, __str__",  # Document those special members
    "undoc-members": True,  # Document members without doc
}

add_module_names = False
default_role = "literal"
todo_include_todos = True

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**/*.inc.rst",
    "spark3dbatch/modules.rst",
]
# bibtex_bibfiles = ["references.bib"]

# -- Check that there is no broken link --------------------------------------
nitpicky = True
nitpick_ignore = [
    # Not recognized by Sphinx, don't know if this is normal
    ("py:class", "optional"),
    ("py:class", "T"),
    ("py:class", "numpy.float64"),
    ("py:class", "numpy.typing.NDArray"),
    ("py:class", "NDArray[np.float64]"),
    ("py:class", "NDArray"),
    ("py:class", "np.float64"),
]

# Link to other libraries
intersphinx_mapping = {
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
    "python": ("https://docs.python.org/3", None),
}

autodoc_type_aliases = {
    "np.float64": "numpy.float64",
    "NDArray": "numpy.typing.NDArray",
    "ElementTree": "xml.etree.ElementTree.ElementTree",
}
# Parameters for sphinx-autodoc-typehints
always_document_param_types = True
always_use_bars_union = True
typehints_defaults = "comma"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_sidebars = {
    "**": [
        "versions.html",
    ],
}

# -- Options for LaTeX output ------------------------------------------------
# https://stackoverflow.com/questions/28454217/how-to-avoid-the-too-deeply-nested-error-when-creating-pdfs-with-sphinx
latex_elements = {"preamble": r"\usepackage{enumitem}\setlistdepth{99}"}


# -- Constants display fix ---------------------------------------------------
# https://stackoverflow.com/a/65195854
def object_description(obj: object) -> str:
    """Format the given object for a clearer printing."""
    return pformat(obj, indent=4)


inspect.object_description = object_description


# -- Bug fixes ---------------------------------------------------------------
# Fix following warning:
# <unknown>:1: WARNING: py:class reference target not found: pathlib._local.Path [ref.class]
# Note that a patch is provided by Sphinx 8.2, but nbsphinx 0.9.7 requires
# sphinx<8.2
# Associated issue:
# https://github.com/sphinx-doc/sphinx/issues/13178
if sys.version_info[:2] >= (3, 13) and sphinx.version_info[:2] < (8, 2):  # type: ignore
    import pathlib

    from sphinx.util.typing import _INVALID_BUILTIN_CLASSES

    _INVALID_BUILTIN_CLASSES[pathlib.Path] = "pathlib.Path"  # type: ignore
    nitpick_ignore.append(("py:class", "pathlib._local.Path"))
