project = "resfo-utilities"
copyright = "2022, Equinor"
author = "Equinor"
release = "1.0.0"


extensions = ["sphinx.ext.autodoc", "sphinx.ext.doctest", "sphinx.ext.intersphinx"]
intersphinx_mapping = {
    "numpy": ("https://numpy.org/doc/stable/", None),
    "python": ("https://docs.python.org/3", None),
}
nitpick_ignore = [
    ("py:class", "np.float32"),
    ("py:class", "numpy.float32"),
    ("py:class", "collections.abc.Buffer"),
    ("py:class", "npt.ArrayLike"),
    ("py:class", "ArrayLike"),
    ("py:class", "npt.NDArray"),
    ("py:class", "np.bool_"),
]
language = "python"
html_theme = "sphinx_rtd_theme"
autodoc_type_aliases = {"npt.ArrayLike": "ArrayLike"}
