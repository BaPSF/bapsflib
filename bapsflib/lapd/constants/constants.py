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
import datetime
import warnings

import astropy.units as u

from astropy.constants import Constant
from astropy.utils.exceptions import AstropyWarning


class BAPSFCONSTANT(Constant):
    default_reference = 'Basic Plasma Science Facility'
    _registry = {}
    _has_incompatible_units = set()


port_spacing = BAPSFCONSTANT('port_spacing', 'LaPD port spacing',
                             31.95, 'cm', 1.0, system='cgs')

ref_port = BAPSFCONSTANT('ref_port', 'LaPD reference port number', 53,
                         u.dimensionless_unscaled, 0, system='cgs')


class MainCathode(object):
    """Constants related to the main LaPD cathode."""

    def __init__(self, operation_date=datetime.datetime.now()):
        super().__init__()

        # define operation_date of interest
        self.operation_date = operation_date

    @property
    def operation_date(self):
        return self._operation_date

    @operation_date.setter
    def operation_date(self, val: datetime):
        # do a date condition when "new" main cathode is installed
        self._operation_date = val

        with warnings.catch_warnings():
            warnings.simplefilter('ignore', AstropyWarning)

            if val.year <= val.year:
                self.diameter = BAPSFCONSTANT(
                    'diameter',
                    "Diameter of LaPD's main cathode",
                    60.0, 'cm',
                    1.0, system='cgs'
                )
                self.z = BAPSFCONSTANT(
                    'z',
                    "Axial location of LaPD's main cathode",
                    1700.0, 'cm',
                    1.0, system='cgs'
                )
                self.anode_z = BAPSFCONSTANT(
                    'anode_z',
                    "Axial location of LaPD's main anode",
                    1650.0, 'cm',
                    1.0, system='cgs'
                )
                self.cathode_descr = "barium-oxide coated nickle"
                self.lifespan = (NotImplemented, NotImplemented)
