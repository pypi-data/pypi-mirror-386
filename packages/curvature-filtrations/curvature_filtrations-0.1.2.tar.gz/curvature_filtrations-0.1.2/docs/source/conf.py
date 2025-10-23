# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = "SCOTT"
copyright = "2024, Jeremy Wayland, Emily Simons, and Bastian Rieck"
author = "Jeremy Wayland, Emily Simons, and Bastian Rieck"
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.linkcode",
]
# Ensure that member functions are documented. These are sane defaults.
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
templates_path = ["_templates"]
exclude_patterns = []
# Tries to assign some semantic meaning to arguments provided with
# single backtics, such as `x`. This way, we can ignore `func` and
# `class` targets etc. (They still work, though!)
default_role = "obj"
html_theme = "furo"
# html_logo = "../../TARDIS.svg"
html_static_path = ["_static"]
# Ensures that modules are sorted correctly. Since they all pertain to
# the same package, the prefix itself can be ignored.
# modindex_common_prefix = ["scott."]
html_theme_options = {
    "source_repository": "https://github.com/aidos-lab/curvature-filtrations/",
    "source_branch": "main",
    "source_directory": "docs/source/",
}


# Specifies how to actually find the sources of the modules. Ensures
# that people can jump to files in the repository directly.
def linkcode_resolve(domain, info):
    # Let's frown on global imports and do everything locally as much as
    # we can.
    import sys
    import scott

    if domain != "py":
        return None
    if not info["module"]:
        return None

    # Attempt to identify the source file belonging to an `info` object.
    # This code is adapted from the Sphinx configuration of `numpy`; see
    # https://github.com/numpy/numpy/blob/main/doc/source/conf.py.
    def find_source_file(module):
        obj = sys.modules[module]
        for part in info["fullname"].split("."):
            obj = getattr(obj, part)
        import inspect
        import os

        fn = inspect.getsourcefile(obj)
        fn = os.path.relpath(fn, start=os.path.dirname(scott.__file__))
        source, lineno = inspect.getsourcelines(obj)
        return fn, lineno, lineno + len(source) - 1

    try:
        module = info["module"]
        source = find_source_file(module)
    except Exception:
        source = None
    root = f"https://github.com/aidos-lab/curvature-filtrations/tree/main/{project.lower()}/"
    if source is not None:
        fn, start, end = source
        return root + f"{fn}#L{start}-L{end}"
    else:
        return None
