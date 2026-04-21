"""
Module containing the main
`~bapsflib._hdf.utils.hdfreaddata.HDFReadData` class.
"""

__all__ = ["HDFReadData"]

import astropy.units as u
import copy
import numpy as np
import os
import time

from typing import Union, TYPE_CHECKING, Tuple
from warnings import warn

from bapsflib._hdf.utils.file import File
from bapsflib._hdf.utils.hdfreadcontrols import HDFReadControls
from bapsflib._hdf.utils.helpers import (
    build_shotnum_dset_relation,
    condition_controls,
    condition_shotnum,
    do_shotnum_intersection,
)
from bapsflib.utils.warnings import BaPSFWarning, HDFMappingWarning

if TYPE_CHECKING:  # pragma: no cover
    # This is done for typing purposes only.  A full import is not needed.
    import h5py
    from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate


def _condition_hdf_file(hdf_file: File):
    # Condition the `hdf_file` argument for HDFReadData
    #
    if not isinstance(hdf_file, File):
        raise TypeError(
            f"`hdf_file` is NOT type `{File.__module__}.{File.__qualname__}`"
        )

    return hdf_file


def _condition_add_controls(hdf_file: File, add_controls):
    # Condition the `add_controls` agrument for HDFReadData.
    #
    _map = hdf_file.file_map

    # Check for non-empty controls
    if bool(add_controls) and not bool(_map.controls):
        raise ValueError("There are no control devices in the HDF5 file.")

    # condition controls
    if bool(add_controls):
        controls = condition_controls(hdf_file, add_controls)
    else:
        controls = []

    return controls


def _condition_digitizer(hdf_file: File, digitizer) -> HDFMapDigiTemplate:
    # Condition the `digitizer` agrument for HDFReadData.
    #
    _map = hdf_file.file_map

    if not bool(_map.digitizers):
        raise ValueError("There are no digitizers in the HDF5 file.")
    elif digitizer is None:
        if not bool(_map.main_digitizer):
            raise ValueError(
                "No main digitizer is identified...need to specify the "
                "`digitizer` keyword argument."
            )

        warn(
            f"Digitizer not specified so assuming the 'main_digitizer' "
            f"({_map.main_digitizer.device_name}) defined in the mappings.",
            BaPSFWarning,
        )
        _dmap = _map.main_digitizer
    else:
        try:
            _dmap = _map.digitizers[digitizer]
        except KeyError:
            raise ValueError(
                f"Specified Digitizer '{digitizer}' is not among known "
                f"digitizers ({list(_map.digitizers)})"
            )

    return _dmap


def _condition_time_slice(time_slice: slice, dset: h5py.Dataset) -> Tuple[slice, int]:
    if not isinstance(time_slice, slice):
        raise TypeError(
            f"Argument `time_slice` must be a slice object, got type {type(time_slice)}."
        )

    if time_slice == slice(None):
        return time_slice, int(dset.shape[1])

    step = time_slice.step
    if step is not None and step <= 0:
        raise ValueError(
            f"Argument `time_slice` must have a positive step, got {step}."
        )

    start, stop, step = time_slice.indices(dset.shape[1])
    if start is None or stop is None:
        pass
    elif stop == start:
        raise ValueError(
            f"Arguement `time_slice` must have differing start and stop "
            f"indices, otherwise the returned data will be NULL.  "
            f"start = stop = {start}"
        )
    elif stop < start:
        raise ValueError(
            f"Argument `time_slice` must have a starting index less than "
            f"the stop index, but got start ({start}) > stop ({stop})."
        )

    ntime = len(range(*time_slice.indices(dset.shape[1])))
    if ntime == 0:
        raise ValueError(
            f"Argument `time_slice` ({time_slice}) will result in a "
            f"NULL array."
        )

    return slice(start, stop, step), ntime


def _generate_shotnum_sni_index(
        shotnum,
        index,
        dheader: h5py.Dataset,
        shotnumkey: str | None,
        intersection_set: bool,
):
    # Build the sni, index, and shotnum arrays such that
    #
    #   shotnum[sni] = dheader[index, shotnumkey]
    #
    # index   -- row index of digitizer dataset
    #            ~ indexed at 0
    #            ~ supersedes any other indexing keywords
    # shotnum -- global HDF5 file shot number
    #            ~ this is the index used to link values between datasets
    #            ~ overridden by `index`
    #
    # Through conditioning the following are (re-)defined
    # index   -- row index of digitizer dataset (dset)
    #            ~ numpy.ndarray
    #            ~ dtype = np.integer
    #            ~ shape = (num_of_indices,)
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
    #            ~ shotnum[sni] = dheader[index, shotnumkey]
    #            ~ data['signal'][sni, ...] = dset[index, ...]
    #            ~ data['singal'][np.logical_not(sni), ...] = np.nan
    #            ~ numpy.ndarray
    #            ~ dtype = np.bool
    #            ~ shape = (sn_size, )
    #            ~ np.count_nonzero(arr[0,...]) = num_of_indices
    #
    # - Indexing behavior: (depends on intersection_set)
    #
    #   ~ intersection_set = True (DEFAULT)
    #     * the returned array will only contain shot numbers that
    #       are in the intersection of shotnum, the digitizer
    #       dataset, and all the specified control device datasets
    #
    #   ~ intersection_set = False
    #     * the returned array will contain all shot numbers
    #       specified by shotnum (>= 1)
    #     * if a dataset does not included a shot number contained
    #       in shotnum, then its entry in the returned array will
    #       be given a NULL value depending on the dtype
    #
    # Determine if indexing w.r.t. `index` or `shotnum`
    index_with = "index"
    if (
        (isinstance(index, slice) and index == slice(None))
        and (not isinstance(shotnum, slice) or shotnum != slice(None))
    ):
        index_with = "shotnum"

    # Condition `index` and `shotnum` keywords
    # - Valid indexing types are: int, list(int), slice(), and
    #   np.ndarray
    #
    if index_with == "index":
        # Condition `index` keyword
        #
        # Note: I'm letting the slicing of dset[index, shotnumkey]
        #       throw the appropriate errors
        #
        # Define `shotnum`
        # - Note: h5py datasets can NOT be sliced using numpy arrays
        #
        # convert `index` to np.ndarray
        sn_size = dheader.size
        if isinstance(index, int):
            index = np.array([index], dtype=np.int32)
        elif isinstance(index, list):
            index = np.array(index, dtype=np.int32)
        elif isinstance(index, slice):
            start, stop, step = index.indices(sn_size)
            index = np.arange(start, stop, step, dtype=np.int32)
        elif isinstance(index, type(Ellipsis)):
            index = np.arange(0, sn_size, 1, dtype=np.int32)
        elif isinstance(index, np.ndarray):
            pass
        else:
            raise TypeError("Valid `index` type not passed.")

        # convert (VALID) negative indices to positive
        neg_index_mask = np.where((index < 0) & (index >= -sn_size), True, False)
        if np.any(neg_index_mask):
            adj_ii = index[neg_index_mask] % sn_size
            index[neg_index_mask] = adj_ii
        index = np.unique(index)

        # define `shotnum`
        if shotnumkey is not None:
            shotnum = dheader[index.tolist(), shotnumkey]
        else:
            # The header dataset for the associated digitizer does NOT
            # contain shot number information.  Assume the shot number
            # is the index value plus one
            shotnum = index + 1

        # define sni
        sni = np.ones(shotnum.shape[0], dtype=bool)

    else:
        # perform `shotnum` conditioning
        # - `shotnum` is returned as a numpy array
        shotnum = condition_shotnum(shotnum, [dheader], [shotnumkey])

        # Calc. the corresponding `index` and `sni`
        # - `shotnum` will be converted from list to np.array
        # - `index` and `sni` will be np.array's
        #
        index, sni = build_shotnum_dset_relation(
            shotnum=shotnum,
            dset=dheader,
            shotnumkey=shotnumkey,
            n_configs=1,
            config_column_value=None,
        )

        # perform intersection
        if intersection_set:
            shotnum, sni_dict, index_dict = do_shotnum_intersection(
                shotnum, {"digi": {"signal": sni}}, {"digi": {"signal": index}}
            )
            sni = sni_dict["digi"]["signal"]
            index = index_dict["digi"]["signal"]

    return shotnum, sni, index


class HDFReadData(np.ndarray):
    """
    Reads digitizer and control device data from the HDF5 file. Control
    device data is extracted using `~.hdfreadcontrols.HDFReadControls`
    and combined with the digitizer data.

    This class constructs and returns a structured numpy array.  The
    data in the array is grouped into three categories:

    #. shot numbers which are contained in the ``'shotnum'`` field
    #. digitizer data which is contained in the ``'signal'`` field
    #. control device data which is represented by the remaining fields
       in the numpy array.  These field names are polymorphic and are
       defined by the control device mapping class. (see
       `~.hdfreadcontrols.HDFReadControls` for more detail)

    Data that is not shot number specific is stored in the :attr:`info`
    attribute.

    .. note::

        * Every returned `numpy` array will have the ``'xyz'`` field,
          which is reserved for probe position data.  If a specified
          control device (via keyword ``add_controls``) contains
          position data, then this field will be auto populated;
          otherwise, the field will be filled with `numpy.nan` values.
    """

    def __new__(
        cls,
        hdf_file: File,
        board: int,
        channel: int,
        index=slice(None),
        shotnum=slice(None),
        time_slice=slice(None),
        digitizer=None,
        config_name=None,
        adc=None,
        keep_bits=False,
        add_controls=None,
        intersection_set=True,
        **kwargs,
    ):
        """
        Parameters
        ----------
        hdf_file : `~bapsflib._hdf.utils.file.File`
            HDF5 file object

        board : `int`
            analog-digital-converter board number

        channel : `int`
            analog-digital-converter channel number

        index : Union[int, List[int], slice, numpy.ndarray], optional
            dataset row indices to be sliced. Overridden by argument
            ``shotnum``. (DEFAULT ``slice(None)``)

        shotnum : Union[int, List[int], slice, numpy.ndarray], optional
            HDF5 file shot number(s) indicating data entries to be
            extracted.  Overrides argument ``index``.  (DEFAULT
            ``slice(None)``)

        digitizer : `str`, optional
            name of the digitizer

        adc : `str`, optional
            name of the analog-digital-converter

        config_name : `str`, optional
            name of the digitizer configuration

        keep_bits : `bool`, optional
            set `True` to keep data in bits, `False` (DEFAULT) to
            convert data to voltage

        add_controls : Union[str, Iterable[str, Tuple[str, Any]]], optional
            a list indicating the desired control device names and their
            configuration name (if more than one configuration exists)

        intersection_set : `bool`, optional
            `True` (DEFAULT) will force the returned shot numbers to be
            the intersection of ``shotnum`` and the shot numbers
            contained in each control device and digitizer dataset.
            `False` will return the union of shot numbers.

        Notes
        -----

        Behavior of ``index``, ``shotnum`` and ``intersection_set``:

        .. note::

            * The ``shotnum`` keyword will always override the
              ``index`` keyword, but, due to extra overhead
              required for identifying shot number locations in the
              digitizer dataset, the ``index`` keyword will always
              execute quicker than the ``shotnum`` keyword.

        Examples
        --------

        Here data is extracted from the digitizer ``'SIS crate'`` and
        position data is mated from the control device ``'6K Compumotor'``.

        >>> # open HDF5 file
        >>> f = bapsflib.lapd.File('test.hdf5')
        >>>
        >>> # read digitizer data from board 1, channel 1,
        >>> # - this is equivalent to
        >>> #   f.read_data(1, 1)
        >>> data = HDFReadData(f, 1, 1)
        >>> data.dtype
        dtype([('shotnum', '<u4'), ('signal', '<f4', (100,)),
              ('xyz', '<f4', (3,))])
        >>>
        >>> # display shot numbers
        >>> data['shotnum']
        array([  1,  2, ..., 98, 99], dtype=uint32)
        >>>
        >>> # show 'signal' values for shot number 1
        >>> data['signal'][0]
        array([-0.41381955, -0.4134333 , -0.4118886 , ..., -0.41127062,
               -0.4105754 , -0.41119337], dtype=float32)
        >>>
        >>> # show 'xyz' values for shot number 1
        >>> data['xyz'][0]
        array([nan, nan, nan], dtype=float32)
        >>>
        >>> # read digitizer data while adding '6K Compumotor' data
        >>> # from receptacle (configuration) 3
        >>> data = HDFReadData(
        ...     f, 1, 1, add_controls=[('6K Compumotor', 3)]
        ... )
        >>> data.dtype
        dtype([('shotnum', '<u4'), ('signal', '<f4', (100,)),
               ('xyz', '<f4', (3,)), ('ptip_rot_theta', '<f8'),
               ('ptip_rot_phi', '<f8')])
        >>>
        >>> # show 'xyz' values for shot number 1
        >>> data['xyz'][0]
        array([ -32. ,   15. , 1022.4], dtype=float32)

        """

        # Condition arguments
        hdf_file = _condition_hdf_file(hdf_file)
        controls = _condition_add_controls(hdf_file, add_controls)
        _dmap = _condition_digitizer(hdf_file, digitizer)
        _fmap = hdf_file.file_map
        config_name, adc = _dmap.validate_config_name_and_adc(config_name, adc)

        # construct dataset names and internal HDF5 paths
        #
        # dname : digitizer dataset name
        # dhname : digitizer header dataset name
        # dpath : full path to digitizer group
        #
        # Note: _dmap.construct_dataset_name has conditioning for
        #       board and channel
        #
        dname, d_info = _dmap.construct_dataset_name(
            board=board,
            channel=channel,
            config_name=config_name,
            adc=adc,
            return_info=True,
        )
        dhname = _dmap.construct_header_dataset_name(
            board=board,
            channel=channel,
            config_name=config_name,
            adc=adc,
        )
        dpath = f"{_dmap.info['group path']}/"

        # get datasets
        #  dset : digitizer h5py.Dataset object
        #  dheader : header dataset related to dset
        #
        dset = hdf_file.get(dpath + dname)
        dheader = hdf_file.get(dpath + dhname)

        # define `shotnumkey`
        # - field name for shot number column in dheader
        #
        shotnum_config = _dmap.configs[config_name]["shotnum"]
        shotnumkey = None if shotnum_config is None else shotnum_config["dset field"][0]

        # Generate the shotnum, sni, and index arrays with only the
        # digitizer datasets
        #
        # The generated arrays form the relation
        #
        #   shotnum[sni] = dheader[index, shotnumkey]
        #
        shotnum, sni, index = _generate_shotnum_sni_index(
            shotnum=shotnum,
            index=index,
            dheader=dheader,
            shotnumkey=shotnumkey,
            intersection_set=intersection_set,
        )

        # Read control data
        if len(controls) != 0:
            cdata = HDFReadControls(
                hdf_file,
                controls,
                assume_controls_conditioned=True,
                shotnum=shotnum,
                intersection_set=intersection_set,
            )

            # re-filter index, shotnum, and sni
            # - only need to be filtered if intersection_set=True
            # - for intersection_set=True, shotnum and index are
            #   one-to-one
            #
            if intersection_set:
                new_sn_mask = np.isin(shotnum, cdata["shotnum"])
                shotnum = shotnum[new_sn_mask]
                index = index[new_sn_mask]
                sni = np.ones(shotnum.shape[0], dtype=bool)
        else:
            cdata = None

        # validate time slicing
        time_slice, ntime = _condition_time_slice(time_slice, dset)

        # Define dtype and shape
        sigtype = np.float32 if not keep_bits else dset.dtype
        shape = shotnum.shape
        dtype = [
            ("shotnum", np.uint32, ()),
            ("signal", sigtype, (ntime,)),
            ("xyz", np.float32, (3,)),
        ]
        if len(controls) != 0:
            for subdtype in cdata.dtype.descr:
                if subdtype[0] not in [d[0] for d in dtype]:
                    dtype.append(subdtype)

        # Initialize data array
        data = np.empty(shape, dtype=dtype)

        # Populate "shotnum"
        data["shotnum"] = shotnum

        # Populate "signal"
        index = index.tolist()
        if intersection_set:
            # fill signal
            data["signal"][...] = dset[index, time_slice]
        else:
            # fill signal
            data["signal"][sni, ...] = dset[index, time_slice]
            if np.issubdtype(data["signal"].dtype, np.integer):
                data["signal"][np.logical_not(sni)] = 0
            else:
                # dtype is np.floating
                data["signal"][np.logical_not(sni)] = np.nan

        # Populate fields related to controls (e.g. "xyz")
        if len(controls) != 0:
            # Note: shot numbers of cdata and data are one-to-one
            #       by this point so intersection_set is irrelevant
            #
            if not np.array_equal(data["shotnum"], cdata["shotnum"]):  # pragma: no cover
                # this should never happen
                raise ValueError("data['shotnum'] and cdata['shotnum'] are not equal")

            # fill xyz
            if "xyz" in cdata.dtype.names:
                data["xyz"] = cdata["xyz"]
            else:
                data["xyz"] = np.nan

            # fill remaining controls
            for field in cdata.dtype.names:
                if field not in ("shotnum", "xyz"):
                    data[field] = cdata[field]
        else:
            # fill xyz
            data["xyz"] = np.nan

        # Define obj to be returned
        obj = data.view(cls)

        # get voltage offset
        try:
            _signal_units = u.bit if keep_bits else u.volt
            if d_info["bit"] is None:
                # Since no bit value is recorded, the digitizer data must
                # have been saved as voltage.
                keep_bits = True
                voffset = None
                _signal_units = u.volt
            else:
                voffset = dheader[index[0], "Offset"]

            if voffset == 0:
                warn(
                    "Digitizer header dataset voltage 'Offset' field is zero.  "
                    "This will produce a NULL voltage array if the bit "
                    "conversion is attempted.  Leaving the data as bits.",
                    BaPSFWarning,
                )
                keep_bits = True
                voffset = None
                _signal_units = None
            elif voffset is not None:
                voffset = voffset * u.volt

        except ValueError:
            warn(
                "Digitizer header dataset is missing the voltage 'Offset' field.",
                HDFMappingWarning,
            )
            voffset = None
            _signal_units = None
        except IndexError as err:  # pragma: no cover
            warn(
                f"{err} ... Digitizer header dataset is being index out of "
                f"range, unable to determine the voltage 'Offset'.",
                HDFMappingWarning,
            )
            voffset = None
            _signal_units = None

        # assign dataset meta-info
        obj._info = {
            "source file": os.path.abspath(hdf_file.filename),
            "device group path": _dmap.info["group path"],
            "device dataset path": dpath + dname,
            "digitizer": d_info["digitizer"],
            "configuration name": d_info["configuration name"],
            "adc": d_info["adc"],
            "bit": d_info["bit"],
            "clock rate": d_info["clock rate"],
            "sample average": d_info["sample average (hardware)"],
            "shot average": d_info["shot average (software)"],
            "board": board,
            "channel": channel,
            "voltage offset": voffset,
            "probe name": None,
            "port": (None, None),
            "signal units": _signal_units,
            "time_dset_path": d_info.get("time_dset_path", None),
        }

        if obj._info["time_dset_path"] is not None:
            obj._info["time_dset_path"] = dpath + obj._info["time_dset_path"]

        if cdata is not None:
            obj._info["controls"] = copy.deepcopy(cdata.info["controls"])
        else:
            obj._info["controls"] = {}

        # convert to voltage
        # - 'signal' dtype is assigned based on keep_bit
        #
        # obj['signal'] = obj['signal'].astype(np.float32, copy=False)
        #
        if not keep_bits:
            if obj.dv is None:
                warn(
                    "Unable to calculated voltage step size...'signal' remains as bits",
                    BaPSFWarning,
                )
            else:
                # define offset
                offset = abs(obj.info["voltage offset"].value)

                # calc voltage
                obj["signal"] = (obj.dv.value * obj["signal"]) - offset

                # update 'signal units'
                obj._info["signal units"] = u.volt

        # return obj
        return obj

    def __array_finalize__(self, obj):
        # This should only be True during explicit construction
        # if obj is None:
        if obj is None or obj.__class__ is np.ndarray:
            return

        # Define _info attribute
        self._info = getattr(
            obj,
            "_info",
            {
                "source file": None,
                "device group path": None,
                "device dataset path": None,
                "configuration name": None,
                "adc": None,
                "bit": None,
                "clock rate": None,
                "sample average": None,
                "shot average": None,
                "board": None,
                "channel": None,
                "voltage offset": None,
                "probe name": None,
                "port": (None, None),
                "signal units": None,
                "controls": {},
            },
        )

    def convert_signal(self, to_volt=False, to_bits=False, force=False):
        """converts signal from volts (bits) to bits (volts)"""
        #
        # 1. investigate if 'signal' values are np.integer or
        #    np.floating
        #    - np.integer => 'signal' is in bits
        #    - np.floating => 'signal' is in volts
        # 2. only convert if requested conversion is not current state
        # 3. update 'signal units' in self._info
        #
        raise NotImplementedError

    @property
    def info(self):
        """
        A dictionary of metadata for the extracted data. The
        dict() keys are:

        .. list-table::
            :widths: 5 3 11

            * - ``"source file"``
              - `str`
              - full path of the HDF5 file the data was retrieved from
            * - ``"device group path"``
              - `str`
              - internal HDF5 path to the device group
            * - ``"device dataset path"``
              - `str`
              - internal HDF5 path to the data originating dataset
            * - ``"digitizer"``
              - `str`
              - digitizer name
            * - ``"configuration name"``
              - `str`
              - name of data configuration
            * - ``"adc"``
              - `str`
              - analog-digital converter in which the data was recorded
                on
            * - ``"bit"``
              - `int` | `None`
              - bit resolution for the adc
            * - ``"clock rate"``
              - `astropy.Quantity` | `None`
              - digitizing clock rate of the adc
            * - ``"sample average"``
              - `int` | None
              - (hardware sampling) number of data samples averaged
                together
            * - ``"shot average"``
              - `int` | None
              - (software averaging) number of shot sequences averaged
                together
            * - ``"board"``
              - `int`
              - adc board the data was retrieved from
            * - ``"channel"``
              - `int`
              - adc channel the data was retrieved from
            * - ``"voltage offset"``
              - `float` | None
              - half the peak-to-peak voltage range of the adc
            * - ``"probe name"``
              - `str` | None
              - name of deployed probe...empty for user to use at
                his/her discretion
            * - ``"port"``
              - (`int`, `str`)
              - 2-element tuple indicating which port the probe was
                deployed on, eg. (19, 'W')
            * - ``"signal units"``
              - `astropy.Unit`
              - units of the returned ``"signal"`` data
            * - ``"time_dset_path"``
              - `str` | None
              - internal HDF5 path to a time array dataset (if present)
            * - ``"controls"``
              - `dict`
              - meta-data of the control device data included in the
                data read


        .. 'port' -- 2-element tuple indicating which port the probe was
                     deployed on. e.g. (19, 'W') => deployed on port 19
                     on the west side of the machine. Second elements
                     descriptors should follow:
                     'T'  = top
                     'TW' = top-west
                     'W'  = west
                     'BW' = bottom-west
                     'B'  = bottom
                     'BE' = bottom-east
                     'E'  = east
                     'TE' = top-east
        """
        return self._info

    @property
    def dt(self) -> Union[u.Quantity, None]:
        r"""
        Temporal step size (in sec) calculated from the ``'clock rate'``
        and ``'sample average'`` items in :attr:`info`.  Returns `None`
        if step size can not be calculated.

        .. math::

            dt = \frac{\text{sample average}}{\text{clock rate}}
        """
        if not isinstance(self.info["clock rate"], u.Quantity):
            return

        # calc base dt
        dt = 1.0 / self.info["clock rate"]
        dt = dt.to("s")

        # adjust for hardware averaging
        if self.info["sample average"] is not None:
            dt = dt * float(self.info["sample average"])

        return dt

    @property
    def dv(self) -> Union[u.Quantity, None]:
        """
        Voltage step size (in volts) calculated from the ``'bit'`` and
        ``'voltage offset'`` items in :attr:`info`.  Returns `None` if
        step size can not be calculated.
        """
        if self.info["voltage offset"] is None:
            return
        elif self.info["bit"] is None:
            return

        dv = 2.0 * abs(self.info["voltage offset"]) / (2.0 ** self.info["bit"] - 1.0)
        return dv
