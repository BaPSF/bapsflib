#!/usr/bin/env python3
#
# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2020 Erik T. Everson and BaPSF Contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
import codecs
import os
import re

from setuptools import setup
from setuptools.config import read_configuration

# find here
here = os.path.abspath(os.path.dirname(__file__))


# ---- Define helpers for version-ing                                       ----
# - following 'Single-sourcing the package version' from 'Python
#   Packaging User Guide'
#   https://packaging.python.org/guides/single-sourcing-package-version/
#
def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# ---- Perform setup                                                        ----
setup_params = read_configuration("setup.cfg")["options"]["extras_require"]
setup_params["metadata"]["version"] = find_version("bapsflib", "__init__.py")
setup(**setup_params)
