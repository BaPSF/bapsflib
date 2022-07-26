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
Module containing the main
`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls` class.
"""
__all__ = ["HDFReadControls"]

import copy
import h5py
import numpy as np
import os
import time

from functools import reduce
from typing import Any, Dict, Iterable, List, Tuple, Union
from warnings import warn

from bapsflib._hdf.maps.controls.templates import (
    HDFMapControlCLTemplate,
    HDFMapControlTemplate,
)
from bapsflib._hdf.utils.file import File
from bapsflib._hdf.utils.helpers import (
    build_shotnum_dset_relation,
    condition_controls,
    condition_shotnum,
    do_shotnum_intersection,
)

# define type aliases
ControlMap = Union[HDFMapControlTemplate, HDFMapControlCLTemplate]
ControlsType = Union[str, Iterable[Union[str, Tuple[str, Any]]]]
IndexDict = Dict[str, np.ndarray]


class HDFReadControls(np.ndarray):
    """
    Reads control device data from the HDF5 file.

    This class constructs and returns a structured numpy array.  The
    data in the array is grouped into two categories:

    #. shot numbers which are contained in the :code:`'shotnum'` field
    #. control device data which is represented by the remaining fields
       in the numpy array.  These field names are polymorphic and are
       defined by the control device mapping class.

    Data that is not shot number specific is stored in the :attr:`info`
    attribute.

    .. note::

        * It is assumed that control data is always extracted with the
          intent of being matched to digitizer data.
        * Only one control for each
          :class:`~bapsflib._hdf.maps.controls.types.ConType` can
          be specified at a time.
        * It is assumed that there is only ONE dataset associated with
          each control device configuration.
        * If multiple device configurations are saved in the same HDF5
          dataset (common in the :ibf:`'Waveform'` control device),
          then it is assumed that the configuration writing order is
          consistent for all recorded shot numbers.  That is, if
          *'config1'*, *'config2'*, and *'config3'* are recorded in that
          order for shot number 1, then that order is preserved for all
          recorded shot numbers.
    """

    __example_doc__ = """
    :Example: Here the control device :code:`'Waveform'` is used as a
        basic example:
        
        >>> # open HDF5 file
        >>> f = bapsflib.lapd.File('test.hdf5')
        >>>
        >>> # read control data
        >>> # - this is equivalent to 
        >>> #   f.read_control(['Waveform', 'config01'])
        >>> data = HDFReadControls(f, ['Waveform', 'config01'])
        >>> data.dtype
        dtype([('shotnum', '<u4'), ('command', '<U18')])
        >>>
        >>> # display shot numbers
        >>> data['shotnum']
        array([   1,    2,    3, ..., 6158, 6159, 6160], dtype=uint32)
        >>>
        >>> # show 'command' values for shot numbers 1 to 2
        >>> data['command'][0:2:]
        array(['FREQ 50000.000000', 'FREQ 50000.000000'],
              dtype='<U18')
    """

    def __new__(
        cls,
        hdf_file: File,
        controls: ControlsType,
        shotnum=slice(None),
        intersection_set=True,
        **kwargs,
    ):
        """
        :param hdf_file: HDF5 file object
        :param controls: a list indicating the desired control device
            names and their configuration name (if more than one
            configuration exists)
        :type controls: Union[str, Iterable[str, Tuple[str, Any]]]
        :param shotnum: HDF5 file shot number(s) indicating data
            entries to be extracted
        :type shotnum: Union[int, List[int], slice, numpy.ndarray]
        :param bool intersection_set: :code:`True` (DEFAULT) will force
            the returned shot numbers to be the intersection of
            :data:`shotnum` and the shot numbers contained in each
            control device dataset. :code:`False` will return the union
            instead of the intersection

        Behavior of :data:`shotnum` and :data:`intersection_set`:
            * :data:`shotnum` indexing starts at 1
            * Any :data:`shotnum` values :code:`<= 0` will be thrown out
            * If :code:`intersection_set=True`, then only data
              corresponding to shot numbers that are specified in
              :data:`shotnum` and are in all control datasets will be
              returned
            * If :code:`intersection_set=False`, then the returned array
              will have entries for all shot numbers specified in
              :data:`shotnum` but entries that correspond to control
              datasets that do not have the specified shot number will
              be given a NULL value of :code:`-99999`, :code:`0`,
              :code:`numpy.nan`, or :code:`''`, depending on the
              :code:`numpy.dtype`.
        """
        # initialize timing
        tt = []
        if "timeit" in kwargs:  # pragma: no cover
            timeit = kwargs["timeit"]
            if timeit:
                tt.append(time.time())
            else:
                timeit = False
        else:
            timeit = False

        # ---- Condition `hdf_file`                                 ----
        # - `hdf_file` is a lapd.File object
        #
        if not isinstance(hdf_file, File):
            raise TypeError(
                f"`hdf_file` is NOT type `{File.__module__}.{File.__qualname__}`"
            )

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - hdf_file conditioning: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # ---- Examine file map object                              ----
        # grab instance of _fmap
        _fmap = hdf_file.file_map

        # Check for non-empty controls
        if not bool(_fmap.controls):
            raise ValueError("There are no control devices in the HDF5 file.")

        # ---- Condition 'controls' Argument                        ----
        # - some calling routines (such as, lapd.File.read_data)
        #   already properly condition 'controls', so passing a keyword
        #   'assume_controls_conditioned' allows for a bypass of
        #   conditioning here
        #
        try:
            # check if `controls` was already conditioned
            if not kwargs["assume_controls_conditioned"]:
                controls = condition_controls(hdf_file, controls)
        except KeyError:
            controls = condition_controls(hdf_file, controls)

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - condition controls: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # ---- Condition shotnum                                    ----
        # shotnum -- global HDF5 file shot number
        #            ~ this is the parameter used to link values between
        #              datasets
        #
        # Through conditioning the following are (re-)defined:
        # index   -- row index of the control dataset(s)
        #            ~ numpy.ndarray
        #            ~ dtype = np.integer
        #            ~ shape = (len(controls), num_of_indices)
        #
        # shotnum -- global HDF5 shot numbers
        #            ~ index at 1
        #            ~ will be a filtered version of input kwarg shotnum
        #              based on intersection_set
        #            ~ numpy.ndarray
        #            ~ dtype = np.uint32
        #            ~ shape = (sn_size, )
        #
        # sni     -- bool array for providing a one-to-one mapping
        #            between shotnum and index
        #            ~ shotnum[sni] = cdset[index, shotnumkey]
        #            ~ numpy.ndarray
        #            ~ dtype = np.bool
        #            ~ shape = (len(controls), sn_size)
        #            ~ np.count_nonzero(arr[0,...]) = num_of_indices
        #
        # - Indexing behavior: (depends on intersection_set)
        #
        #   ~ shotnum
        #     * intersection_set = True
        #       > the returned array will only contain shot numbers that
        #         are in the intersection of shotnum and all the
        #         specified control device datasets
        #
        #     * intersection_set = False
        #       > the returned array will contain all shot numbers
        #         specified by shotnum (>= 1)
        #       > if a dataset does not included a shot number contained
        #         in shotnum, then its entry in the returned array will
        #         be given a NULL value depending on the dtype
        #
        # Gather control datasets and associated shot number field names
        # - things needed to perform the conditioning
        cdset_dict = {}  # type: Dict[str, h5py.Dataset]
        shotnumkey_dict = {}  # type: Dict[str, str]
        for control in controls:
            # control name (cname) and configuration name (cconfn)
            cname = control[0]
            cconfn = control[1]

            # gather control datasets and shotnumkey's
            cmap = _fmap.controls[cname]
            cdset_path = cmap.configs[cconfn]["dset paths"][0]
            cdset_dict[cname] = hdf_file.get(cdset_path)
            shotnumkey = cmap.configs[cconfn]["shotnum"]["dset field"][0]
            shotnumkey_dict[cname] = shotnumkey

        # perform `shotnum` conditioning
        # - `shotnum` is returned as a numpy array
        shotnum = condition_shotnum(shotnum, cdset_dict, shotnumkey_dict)

        # ---- Build `index` and `sni` arrays for each dataset      ----
        #
        # - Satisfies the condition:
        #
        #       shotnum[sni] = dset[index, shotnumkey]
        #
        # Notes:
        # 1. every entry in `index_dict` and `sni_dict` will be a numpy
        #    array
        # 2. all entries in `index_dict` and `sni_dict` are build with
        #    respect to shotnum
        #
        index_dict = {}  # type: IndexDict
        sni_dict = {}  # type: IndexDict
        for control in controls:
            # control name (cname) and configuration name (cconfn)
            cname = control[0]
            cconfn = control[1]
            cmap = _fmap.controls[cname]

            # build `index` and `sni` for each dataset
            index_dict[cname], sni_dict[cname] = build_shotnum_dset_relation(
                shotnum, cdset_dict[cname], shotnumkey_dict[cname], cmap, cconfn
            )

        # re-filter `index`, `shotnum`, and `sni` if intersection_set
        # requested
        if intersection_set:
            shotnum, sni_dict, index_dict = do_shotnum_intersection(
                shotnum, sni_dict, index_dict
            )

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - condition shotnum: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # ---- Build obj                                            ----
        # Define dtype and shape for numpy array
        shape = shotnum.shape
        dtype = [("shotnum", np.uint32, 1)]
        for control in controls:
            # control name (cname) and configuration name (cconfn)
            cname = control[0]
            cconfn = control[1]

            # add fields
            cconfig = _fmap.controls[cname].configs[cconfn]
            for field_name, fconfig in cconfig["state values"].items():
                dtype.append(
                    (
                        field_name,
                        fconfig["dtype"],
                        fconfig["shape"],
                    )
                )

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - define dtype: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # Initialize Control Data
        data = np.empty(shape, dtype=dtype)
        data["shotnum"] = shotnum

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - initialize data np.ndarray: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # Assign Control Data to Numpy array
        for control in controls:
            # control name (cname) and configuration name (cconfn)
            cname = control[0]
            cconfn = control[1]

            # get control dataset
            cmap = _fmap.controls[cname]
            cconfig = cmap.configs[cconfn]
            cdset = cdset_dict[cname]
            sni = sni_dict[cname]
            index = index_dict[cname].tolist()  # type: List

            # populate control data array
            # 1. scan over numpy fields
            # 2. scan over the dset fields that will fill the numpy
            #    fields
            # 3. split between a command list fill or a direct fill
            # 4. NaN fill if intersection_set = False
            #
            for nf_name, fconfig in cconfig["state values"].items():
                # nf_name = the numpy field name
                # fconfig = the mapping dictionary for nf_name
                #
                for npi, df_name in enumerate(fconfig["dset field"]):
                    # df_name
                    #   the dset field name that will fill the numpy
                    #   field
                    # npi
                    #   the index of the numpy array corresponding to
                    #   nf_name that df_name will fill
                    #
                    # assign data
                    if cmap.has_command_list:
                        # command list fill
                        # get command list
                        cl = fconfig["command list"]

                        # retrieve the array of command indices
                        ci_arr = cdset[index, df_name]

                        # assign command values to data
                        for ci, command in enumerate(cl):
                            # Order of operations
                            # 1. find where command index (ci) is in the
                            #    command index array (ci_arr)
                            # 2. construct a new sni for ci
                            # 3. fill data
                            #
                            # find where ci is in ci_arr
                            ii = np.where(ci_arr == ci, True, False)

                            # construct new sni
                            sni_for_ci = np.zeros(sni.shape, dtype=bool)
                            sni_for_ci[np.where(sni)[0][ii]] = True

                            # assign values
                            data[nf_name][sni_for_ci] = command
                    else:
                        # direct fill (NO command list)
                        try:
                            arr = cdset[index, df_name]
                        except ValueError as err:
                            mlist = [1] + list(data.dtype[nf_name].shape)
                            size = reduce(lambda x, y: x * y, mlist)
                            dtype = data.dtype[nf_name].base
                            if df_name == "":
                                # a mapping module gives an empty string
                                # '' when the dataset does not have a
                                # necessary field but you want the read
                                # out to still function
                                # - e.g. 'xyz' but the dataset only
                                #   contains values of 'x' and 'z'
                                #   (the NI_XZ module)
                                #
                                # create zero array
                                arr = np.zeros((len(index),), dtype=dtype)
                            elif size > 1:
                                # expected field df_name is missing but
                                # belongs to an array
                                warn(
                                    f"Dataset missing field '{df_name}', applying "
                                    f"NaN fill to to data array"
                                )
                                arr = np.zeros((len(index),), dtype=dtype)

                                # NaN fill
                                if np.issubdtype(dtype, np.signedinteger):
                                    # any signed-integer
                                    # unsigned has a 0 fill
                                    arr[:] = -99999
                                elif np.issubdtype(dtype, np.floating):
                                    # any float type
                                    arr[:] = np.nan
                                elif np.issubdtype(dtype, np.flexible):
                                    # string, unicode, void
                                    # np.zero satisfies this
                                    pass
                                else:  # pragma: no cover
                                    # no real NaN concept exists
                                    # - this shouldn't happen though
                                    warn(
                                        f"dtype ({dtype}) of {nf_name} has no NaN "
                                        f"concept...no NaN fill done"
                                    )
                            else:
                                # expected field df_name is missing
                                raise err

                        if data.dtype[nf_name].shape != ():
                            # field contains an array (e.g. 'xyz')
                            # data[nf_name][sni, npi] = \
                            #     cdset[index, df_name]
                            data[nf_name][sni, npi] = arr
                        else:
                            # field is a constant
                            # data[nf_name][sni] = \
                            #     cdset[index, df_name]
                            data[nf_name][sni] = arr

                    # handle NaN fill
                    if not intersection_set:
                        # overhead
                        sni_not = np.logical_not(sni)
                        dtype = data.dtype[nf_name].base

                        #
                        if data.dtype[nf_name].shape != ():
                            ii = np.s_[sni_not, npi]
                        else:
                            ii = np.s_[sni_not]

                        # NaN fill
                        if np.issubdtype(dtype, np.signedinteger):
                            data[nf_name][ii] = -99999
                        elif np.issubdtype(dtype, np.unsignedinteger):
                            data[nf_name][ii] = 0
                        elif np.issubdtype(dtype, np.floating):
                            # any float type
                            data[nf_name][ii] = np.nan
                        elif np.issubdtype(dtype, np.flexible):
                            # string, unicode, void
                            data[nf_name][ii] = ""
                        else:
                            # no real NaN concept exists
                            # - this shouldn't happen though
                            warn(
                                f"dtype ({dtype}) of {nf_name} has no NaN concept"
                                f"...no NaN fill done"
                            )

            # print execution timing
            if timeit:  # pragma: no cover
                tt.append(time.time())
                print(f"tt - fill data - {cname}: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # print execution timing
        if timeit:  # pragma: no cover
            n_controls = len(controls)
            tt.append(time.time())
            print(
                f"tt - fill data array: {(tt[-1] - tt[-n_controls - 2]) * 1.0e3} ms "
                f"(intersection_set={intersection_set})"
            )

        # -- Define `obj`                                           ----
        obj = data.view(cls)

        # -- Populate `_info`                                      ----
        # initialize `_info`
        obj._info = {
            "source file": os.path.abspath(hdf_file.filename),
            "controls": {},
            "probe name": None,
            "port": (None, None),
        }

        # add control meta-info
        for control in controls:
            # control name (cname) and configuration name (cconfn)
            cname = control[0]
            cconfn = control[1]

            # get control dataset
            cmap = _fmap.controls[cname]
            cconfig = cmap.configs[cconfn]  # type: dict

            # populate
            obj._info["controls"][cname] = {
                "device group path": cmap.info["group path"],
                "device dataset path": cconfig["dset paths"][0],
                "contype": cmap.contype,
                "configuration name": cconfn,
            }
            for key, val in cconfig.items():
                if key not in ["dset paths", "shotnum", "state values"]:
                    obj._info["controls"][cname][key] = copy.deepcopy(val)

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - total execution time: {(tt[-1] - tt[0]) * 1.0e3} ms")

        # return obj
        return obj

    def __array_finalize__(self, obj):
        # This should only be True during explicit construction
        # if obj is None:
        if obj is None or obj.__class__ is np.ndarray:
            return

        # Define info attribute
        # (for view casting and new from template)
        self._info = getattr(
            obj,
            "_info",
            {
                "source file": None,
                "controls": None,
                "probe name": None,
                "port": (None, None),
            },
        )

    @property
    def info(self) -> dict:
        """A dictionary of meta-info for the control device."""
        return self._info


# add example to __new__ docstring
HDFReadControls.__new__.__doc__ += "\n"
for line in HDFReadControls.__example_doc__.splitlines():
    HDFReadControls.__new__.__doc__ += f"    {line}\n"
