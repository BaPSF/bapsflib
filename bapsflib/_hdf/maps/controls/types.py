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
"""Module for defining `ConType`."""
__all__ = ["ConType"]

from enum import Enum


class ConType(Enum):
    """Enum of Control Device Types"""

    #: type for motion control devices
    MOTION = "motion"

    #: type for power control devices
    POWER = "power"

    #: type for timing control devices
    TIMING = "timing"

    #: type for waveform control devices
    WAVEFORM = "waveform"

    def __repr__(self):  # pragma: no cover
        return f"contype.{self.name}"
