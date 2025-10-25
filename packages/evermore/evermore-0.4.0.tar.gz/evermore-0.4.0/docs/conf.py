from __future__ import annotations

import evermore

project = evermore.__name__
copyright = evermore.__copyright__
author = evermore.__author__
version = release = evermore.__version__

language = "en"

templates_path = ["_templates"]
html_static_path = ["_static"]
master_doc = "index"
source_suffix = [".rst", ".md"]
pygments_style = "sphinx"
add_module_names = False

exclude_patterns = [
    "_build",
    "**.ipynb_checkpoints",
    "Thumbs.db",
    ".DS_Store",
    ".env",
    ".venv",
]

html_title = f"{project} v{version}"
html_theme = "sphinx_book_theme"
html_theme_options = {
    # "logo_only": True,
    "home_page_in_toc": True,
    "show_navbar_depth": 2,
    "show_toc_level": 2,
    "repository_url": "https://github.com/pfackeldey/evermore",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
}
html_context = {"default_mode": "light"}
html_logo = "../assets/favicon.png"
html_favicon = "../assets/favicon.png"

extensions = [
    "myst_nb",
    # "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    # "sphinx.ext.autosectionlabel",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_togglebutton",
]

myst_enable_extensions = [
    "colon_fence",
    "html_image",
    "deflist",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

nitpick_ignore = [
    ("py:class", "_io.StringIO"),
    ("py:class", "_io.BytesIO"),
]

always_document_param_types = True

autodoc_member_order = "bysource"


mathjax3_config = {
    "tex2jax": {"inlineMath": [["$", "$"], ["\\(", "\\)"]]},
    "tex": {
        "macros": {
            "bm": ["\\boldsymbol{#1}", 1],  # \usepackage{bm}, see mathjax/MathJax#1219
            "pyhf": r"\texttt{pyhf}",
            "Combine": r"\texttt{Combine}",
            "JAX": r"\texttt{JAX}",
            "PyTree": r"\texttt{PyTree}",
        }
    },
}


def setup(app):
    app.add_css_file("styles_sphinx_book_theme.css")
