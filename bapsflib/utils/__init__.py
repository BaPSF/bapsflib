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
Package of developer utilities.
"""
__all__ = ['decorators', 'errors', 'warnings', 'NdarrayToXarray']

from . import (decorators, errors, warnings)


def ndarray_to_xarray(data, arr_name={}):
    import xarray as xr
    names = list(data.dtype.names)
    names.remove('signal')
    coords_dict = {}
    for name in names:
        if name == 'xyz':
            coords_dict["x"] = ("shotnum", data[name][:, 0])
            coords_dict["y"] = ("shotnum", data[name][:, 1])
            coords_dict["z"] = ("shotnum", data[name][:, 2])

        else:
            coords_dict[name] = ("shotnum", data[name])

    # coords_test={names[0]:("shot_index",data[names[0]]),"x":("shot_index",data[names[1]][:,0]),"y":("shot_index",data[names[1]][:,1]),"z":("shot_index",data[names[1]][:,2]),names[2]:("shot_index",data[names[2]]),names[3]:("shot_index",data[names[3]])}
    data_array = xr.DataArray(data['signal'], dims=('shotnum', 'time_index'), coords=coords_dict, name=arr_name)
    return data_array
