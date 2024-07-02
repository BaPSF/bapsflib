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
#
"""
Module containing the main `~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI` class.
"""
__all__ = ["HDFReadMSI"]

import copy
import numpy as np
import os

from bapsflib._hdf.utils.file import File


class HDFReadMSI(np.ndarray):
    """
    Reads MSI diagnostic data from the HDF5 file.

    This class constructs and returns a structured numpy array.  The
    data in the array is grouped in three categories:

    #. shot numbers which are contained in the :code:`'shotnum'` field
    #. metadata data that is both shot number and diagnostic specific
       which is stored in the sub-fields of the :code:`'meta'` field
    #. recorded data arrays which get unique fields based on their
       mapping
       :attr:`~bapsflib._hdf.maps.msi.templates.HDFMapMSITemplate.configs`
       attribute

    Data that is not shot number specific is stored in the :attr:`info`
    attribute.
    """

    __example_doc__ = """
    :Example: Here the :code:`'Discharge'` MSI diagnostic is used 
        as an example:

        >>> # open HDF5 file
        >>> f = bapsflib.lapd.File('test.hdf5')
        >>>
        >>> # read MSI data
        >>> # - this is equivalent to f.read_msi('Discharge')
        >>> mdata = HDFReadMSI(f, 'Discharge')
        >>> mdata.dtype
        dtype([('shotnum', '<i4'),
               ('voltage', '<f4', (2048,)),
               ('current', '<f4', (2048,)),
               ('meta', [('timestamp', '<f8'),
                         ('data valid', 'i1'),
                         ('pulse length', '<f4'),
                         ('peak current', '<f4'),
                         ('bank voltage', '<f4')])])
        >>> # display shot numbers
        >>> mdata['shotnum']
        array([    0, 19251], dtype=int32)
        >>>
        >>> # fields 'voltage' and 'current' belong to data arrays
        >>> # - show first 3 elements of 'voltage' for shot number 0
        >>> mdata['voltage'][0,0:3:]
        array([-46.99707 , -46.844482, -46.99707], dtype=float32)
        >>>
        >>> # display peak current for shot number 0
        >>> mdata['meta']['peak current'][0]
        6127.1323
        >>>
        >>> # the `info` attribute has diagnostic specific data
        >>> mdata.info
        {'current conversion factor': [0.0],
         'device name': 'Discharge',
         'device group path': '/MSI/Discharge',
         'dt': [4.88e-05],
         'source file': '/foo/bar/test.hdf5',
         't0': [-0.0249856],
         'voltage conversion factor': [0.0]}
        >>>
        >>> # get time step for the data arrays
        >>> mdata.info['dt'][0]
        4.88e-05
    """

    def __new__(cls, hdf_file: File, dname: str, **kwargs):
        """
        :param hdf_file: HDF5 file object
        :type hdf_file: :class:`~bapsflib.lapd.File`
        :param str dname: name of desired MSI diagnostic
        """
        # ---- Condition `hdf_file`                                 ----
        # - `hdf_file` is a lapd.File object
        #
        if not isinstance(hdf_file, File):
            raise TypeError(
                f"`hdf_file` is NOT type `{File.__module__}.{File.__qualname__}`"
            )

        # ---- Condition `dname`                                    ----
        # ensure `dname` is a string
        if not isinstance(dname, str):
            raise TypeError("arg `dname` needs to be a str")

        # allow for alias names of MSI diagnostics
        aliases = [
            ("Discharge", ["discharge"]),
            (
                "Gas pressure",
                ["gas pressure", "pressure", "partial pressure", "partial pressures"],
            ),
            ("Heater", ["heater"]),
            (
                "Interferometer array",
                ["interferometer array", "interferometer", "interarr"],
            ),
            ("Magnetic field", ["magnetic field", "b", "bfield"]),
        ]
        for name, alias in aliases:
            if dname.lower() in alias:
                dname = name
                break

        # get diagnostic map
        # - assume if a map is successful, then it is formatted to
        #   work without errors (i.e. no conditioning needed)
        #
        try:
            _map = hdf_file.file_map.msi[dname]
        except KeyError:
            raise ValueError("Specified MSI Diagnostic is not among known diagnostics")

        # ---- Construct shape and dtype for np.ndarray             ----
        #
        # initialize dtype_list
        # - this will be converted into dtype for np.ndarray
        # - should look like:
        #   dtype_list = [
        #       ('shotnum', np.int32, ()),
        #       ('signal', np.int32, (2, 100)),
        #       ('meta',
        #        [('f1', np.float32, ()), ('f2', np.int32, ())],
        #        (2,)),
        #   ]
        #
        # add 'shotnum' field
        dtype_list = [
            (
                "shotnum",
                _map.configs["shotnum"]["dtype"],
                _map.configs["shotnum"]["shape"],
            ),
        ]

        # add signal fields
        for field in _map.configs["signals"]:
            dtype_list.append(
                (
                    field,
                    _map.configs["signals"][field]["dtype"],
                    _map.configs["signals"][field]["shape"],
                ),
            )

        # add 'meta' fields
        # - all 'meta' fields needs to have the same number of rows as
        #   the signal fields
        #
        meta_dtype_list = []
        for field in _map.configs["meta"]:
            # skip the 'shape' field
            if field == "shape":
                continue

            # add to meta_dtype_list
            meta_dtype_list.append(
                (
                    field,
                    _map.configs["meta"][field]["dtype"],
                    _map.configs["meta"][field]["shape"],
                ),
            )

        # add 'meta' to dtype_list
        dtype_list.append(
            ("meta", meta_dtype_list, _map.configs["meta"]["shape"]),
        )

        # define dtype
        dtype = np.dtype(dtype_list)

        # ---- Define and Populate Numpy Array                      ----
        # create empty array
        data = np.empty(_map.configs["shape"], dtype=dtype)

        # fill 'shotnum'
        sn_config = _map.configs["shotnum"]
        for ii, path in enumerate(sn_config["dset paths"]):
            # get dataset
            dset = hdf_file[path]

            # get field
            field = (
                sn_config["dset field"][0]
                if len(sn_config["dset field"]) == 1
                else sn_config["dset field"][ii]
            )

            # fill array
            if ii == 0:
                data["shotnum"] = dset[:, field]
            else:
                # ensure every data set has matching shot numbers
                if not np.array_equal(data["shotnum"], dset[field]):
                    raise ValueError(
                        "Datasets do NOT have the same shot number "
                        "values, do NOT know how to handle"
                    )

        # fill 'signals'
        # TODO: ADD ABILITY TO READ FROM A STRUCTURED DATASET
        # - i.e. 'dset field' is not empty
        sig_config = _map.configs["signals"]
        for field in sig_config:
            if len(sig_config[field]["dset paths"]) == 1:
                # get dataset
                path = sig_config[field]["dset paths"][0]
                dset = hdf_file[path]

                # fill array
                data[field] = dset
            else:
                # there are multiple rows in the dataset
                # (e.g. interferometer)
                # - indices look like
                #   [shot number, device number, time series]
                #
                for ii, path in enumerate(sig_config[field]["dset paths"]):
                    # get dataset
                    dset = hdf_file[path]

                    # fill array
                    data[field][:, ii, ...] = dset

        # fill 'meta'
        # TODO: ADD ABILITY TO READ FROM A REGULAR DATASET
        # - i.e. 'dset field' is empty
        meta_config = _map.configs["meta"]
        for field in meta_config:
            # skip 'shape' key
            if field == "shape":
                continue

            # scan thru all datasets
            for ii, path in enumerate(meta_config[field]["dset paths"]):
                # get dataset
                dset = hdf_file[path]

                # get dset_field
                dset_field = (
                    meta_config[field]["dset field"][0]
                    if len(meta_config[field]["dset field"]) == 1
                    else meta_config[field]["dset field"][ii]
                )

                # fill array
                if len(meta_config[field]["dset paths"]) == 1:
                    data["meta"][field] = dset[dset_field]
                else:
                    # there are multiple rows in the dataset
                    # (e.g. interferometer)
                    # - indices look like
                    #   [shot number, device number, time series]
                    #
                    data["meta"][field][:, ii, ...] = dset[dset_field]

        # ---- Define `obj`                                         ----
        obj = data.view(cls)

        # ---- Define `_info` attribute                             ----
        obj._info = {
            "source file": os.path.abspath(hdf_file.filename),
            "device name": _map.info["group name"],
            "device group path": _map.info["group path"],
        }
        for key, val in _map.configs.items():
            if key not in ["shape", "shotnum", "signals", "meta"]:
                obj._info[key] = copy.deepcopy(val)

        # ---- Return `obj`                                         ----
        return obj

    def __array_finalize__(self, obj):
        # This should only be True during explicit construction
        # if obj is None:
        if obj is None or obj.__class__ is np.ndarray:
            return

        # Define _info attribute
        # (for view casting and new from template)
        self._info = getattr(
            obj,
            "_info",
            {
                "source file": None,
                "device name": None,
                "device group path": None,
            },
        )

    @property
    def info(self):
        """A dictionary of meta-info for the MSI diagnostic."""
        return self._info


# add example to __new__ docstring
HDFReadMSI.__new__.__doc__ += "\n"
for line in HDFReadMSI.__example_doc__.splitlines():
    HDFReadMSI.__new__.__doc__ += f"    {line}\n"
