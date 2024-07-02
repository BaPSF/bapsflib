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
import os

from setuptools import setup

# find here
here = os.path.abspath(os.path.dirname(__file__))

# ---- Perform setup                                                        ----
setup(use_scm_version=True)
