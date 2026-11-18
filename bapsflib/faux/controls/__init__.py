"""
The `bapsflib.faux.controls` module contains all the control device
group generators used by `~bapsflib.faux.builder.FauxHDFBuilder`.
"""

__all__ = [
    "FauxBMotion",
    "FauxN5700PS",
    "FauxNIXYZ",
    "FauxNIXZ",
    "FauxPositions180E",
    "FauxSixK",
    "FauxWaveform",
]

from bapsflib.faux.controls.bmotion import FauxBMotion
from bapsflib.faux.controls.n5700ps import FauxN5700PS
from bapsflib.faux.controls.nixyz import FauxNIXYZ
from bapsflib.faux.controls.nixz import FauxNIXZ
from bapsflib.faux.controls.positions180e import FauxPositions180E
from bapsflib.faux.controls.sixk import FauxSixK
from bapsflib.faux.controls.waveform import FauxWaveform
