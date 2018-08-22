#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2018 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
"""
This :mod:`~bapsflib.lapd.constants` package contains constants relevant
to the setup and configuration of the LaPD.
"""
from .constants import (port_spacing, ref_port, MainCathode)

__all__ = ['MainCathode', 'port_spacing', 'ref_port']
