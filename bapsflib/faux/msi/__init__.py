"""
The `bapsflib.faux.msi` module contains all the MSI device
group generators used by `~bapsflib.faux.builder.FauxHDFBuilder`.
"""

__all__ = [
    "FauxDischarge",
    "FauxGasPressure",
    "FauxHeater",
    "FauxInterferometerArray",
    "FauxMagneticField",
]

from bapsflib.faux.msi.discharge import FauxDischarge
from bapsflib.faux.msi.gaspressure import FauxGasPressure
from bapsflib.faux.msi.heater import FauxHeater
from bapsflib.faux.msi.interarr import FauxInterferometerArray
from bapsflib.faux.msi.magneticfield import FauxMagneticField
