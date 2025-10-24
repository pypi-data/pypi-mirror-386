""" Public version of the EIS Python Analysis Code """

import os
import sys
import setuptools
from itertools import chain
from setuptools.config import read_configuration

# def get_version(rel_path):
#     here = os.path.abspath(os.path.dirname(__file__))
#     with open(os.path.join(here, rel_path)) as fp:
#         for line in fp.read().splitlines():
#             if line.startswith('__version__'):
#                 # __version__ = "0.9.1"
#                 delim = '"' if '"' in line else "'"
#                 return line.split(delim)[1]
#     raise RuntimeError("Unable to find version string.")

def no_dist_is_release(version):
    # Generates proper release version numbers for PyPI
    # To use, ALWAYS set local_scheme = 'no-local-version'
    from setuptools_scm import get_version as scm_get_ver

    if version.distance == 0:
        return str(version.tag)
    else:
	    # note: this already includes the local version
    	return scm_get_ver()

# Read the contents of the README file
setup_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(setup_dir, 'README.md'), encoding='utf-8') as f:
    readme_text = f.read()

####################################################
# Programmatically generate combinations of "extras"
####################################################
extras = read_configuration("setup.cfg")['options']['extras_require']

# Dev is everything
extras['dev'] = list(chain(*extras.values()))

# All is everything but tests and docs
exclude_keys = ("tests", "docs", "dev")
ex_extras = dict(filter(lambda i: i[0] not in exclude_keys, extras.items()))
# Concatenate all the values together for 'all'
extras['all'] = list(chain.from_iterable(ex_extras.values()))

setuptools.setup(
    # version = get_version("eispac/__init__.py"),
    long_description = readme_text,
    long_description_content_type = 'text/markdown',
    extras_require = extras,
    use_scm_version={'version_scheme':no_dist_is_release,
                     'local_scheme':'no-local-version',
                     'write_to': os.path.join('eispac', '_version.py')},
    project_urls = {
        "Data": "https://eis.nrl.navy.mil/",
        "Documentation": "https://eispac.readthedocs.io/"},
    entry_points = {
        "console_scripts": [
            "eis_catalog = scripts.eis_catalog:eis_catalog",
            "eis_explore_raster = scripts.eis_explore_raster:eis_explore_raster",
            "eis_browse_templates = scripts.eis_browse_templates:eis_browse_templates",
            "eis_download_files = scripts.eis_download_files:eis_download_files",
            "eis_fit_files = scripts.eis_fit_files:eis_fit_files",
            "eis_plot_fit = scripts.eis_plot_fit:eis_plot_fit"]
        }
    )
