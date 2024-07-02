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
"""LaPD constants/parameters."""
__all__ = ["port_spacing", "ref_port", "BaPSFConstant", "SouthCathode"]

import astropy.units as u
import datetime
import warnings

from astropy.constants import Constant
from astropy.utils.exceptions import AstropyWarning
from typing import Tuple


class BaPSFConstant(Constant):
    """BaPSF Constant"""

    #: Default reference for the value of a constant.
    default_reference = "Basic Plasma Science Facility"

    _registry = {}
    _has_incompatible_units = set()


#: BaPSF Constant: nominal distance between LaPD ports
port_spacing = BaPSFConstant(
    "port_spacing", "LaPD port spacing", 31.95, "cm", 1.0, system="cgs"
)
port_spacing.__doc__ += ": nominal distance between LaPD ports"

#: BaPSF Constant: LaPD :math:`z = 0` reference port (most Northern
#: port and :math:`+z` points South towards south cathode)
ref_port = BaPSFConstant(
    "ref_port", "LaPD reference port number", 53, u.dimensionless_unscaled, 0, system=None
)
ref_port.__doc__ += (
    ": LaPD :math:`z = 0` reference port (most "
    "Northern port and :math:`+z` points South "
    "towards south cathode)"
)


class SouthCathode(object):
    """
    .. warning::
       The class is currently in development and only contains info on the NiO
       cathode, no LaB6 data or upgrade data.

    Constants related to the South 'main' LaPD cathode.
    """

    def __init__(self, operation_date=datetime.datetime.now()):
        """
        :param operation_date: Date the south 'main' cathode was
            operated (i.e. date of the experiment)
        :type operation_date: :class:`datetime.datetime`

        :Example:

            >>> import datetime
            >>> MC = SouthCathode(datetime.date(2018, 1, 1))

        """
        super().__init__()

        # define operation_date of interest
        self.operation_date = operation_date

    @property
    def operation_date(self) -> datetime.datetime:
        """
        Date the south 'main' cathode was operated (i.e. date of the
        experiment)
        """
        return self._operation_date

    @operation_date.setter
    def operation_date(self, val: datetime.datetime):
        # do a date condition when "new" south cathode is installed
        self._operation_date = val

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", AstropyWarning)

            if val.year <= val.year:
                self._diameter = BaPSFConstant(
                    "diameter",
                    "Diameter of LaPD's south 'main' cathode",
                    60.0,
                    "cm",
                    1.0,
                    system="cgs",
                )
                self._z = BaPSFConstant(
                    "z",
                    "Axial location of LaPD's south 'main' cathode",
                    1700.0,
                    "cm",
                    1.0,
                    system="cgs",
                )
                self._anode_z = BaPSFConstant(
                    "anode_z",
                    "Axial location of LaPD's south 'main' anode",
                    1650.0,
                    "cm",
                    1.0,
                    system="cgs",
                )
                self._cathode_descr = "barium-oxide coated nickel"
                self._lifespan = (NotImplemented, NotImplemented)

    @property
    def anode_z(self) -> BaPSFConstant:
        """LaPD z location of the anode"""
        return self._anode_z

    @property
    def diameter(self) -> BaPSFConstant:
        """Diameter of LaPD's south 'main' cathode"""
        return self._diameter

    @property
    def z(self) -> BaPSFConstant:
        """LaPD z location of the cathode"""
        return self._z

    @property
    def cathode_descr(self) -> str:
        """Brief description of the cathode"""
        return self._cathode_descr

    @property
    def lifespan(self) -> Tuple[datetime.datetime, datetime.datetime]:
        """Operational lifetime of cathode"""
        return self._lifespan
