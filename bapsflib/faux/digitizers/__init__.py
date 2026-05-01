"""
The `bapsflib.faux.digitizers` module contains all the digitzer device
group generators used by `~bapsflib.faux.builder.FauxHDFBuilder`.
"""

__all__ = [
    "FauxSIS3301",
    "FauxSISCrate",
    "FauxLeCroy180E",
]

from bapsflib.faux.digitizers.lecroy180e import FauxLeCroy180E
from bapsflib.faux.digitizers.sis3301 import FauxSIS3301
from bapsflib.faux.digitizers.siscrate import FauxSISCrate
