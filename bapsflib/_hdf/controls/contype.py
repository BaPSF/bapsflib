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
from enum import Enum


class ConType(Enum):
    """Enum of Control Device Types"""
    motion = 'motion'
    power = 'power'
    timing = 'timing'
    waveform = 'waveform'

    def __repr__(self):  # pragma: no cover
        return 'contype.' + self.name
