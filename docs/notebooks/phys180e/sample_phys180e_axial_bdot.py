import numpy as np
from pathlib import Path

from bapsflib import phys180E

# set the baord and channel you want
BOARD = 0
CHANNEL = 1

# define the relative path to your HDF5 file
_HERE = Path.cwd()
_FILENAME = "sample_phys180e_axial_bdot.hdf5"
_FILE = (_HERE / _FILENAME).resolve()

# open your HDF5 file
f = phys180E.File(_FILE)

# read out your data
# - data be a numpy array three fields
#   data["shotnum"] -> your shot number array
#   data["signal"] -> your digitized signal array
#   data["xyz"] -> your probe position array
data = f.read_data(
    BOARD,
    CHANNEL,
    add_controls=["180E_positions"],
    silent=True,
)
time = f.get_time_array(data)

# do you analysis and plotting
...

# close the HDF5 file
f.close()
