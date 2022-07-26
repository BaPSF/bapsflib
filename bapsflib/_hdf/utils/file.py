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
"""Module containing the main HDF5 `~bapsflib._hdf.utils.file.File` class."""
__all__ = ["File"]

import h5py
import os
import warnings

from typing import Any, Dict, List, Tuple, Union

from bapsflib._hdf.maps import HDFMap, HDFMapControls, HDFMapDigitizers, HDFMapMSI


class File(h5py.File):
    """
    Open a HDF5 file created at the Basic Plasma Science Facility.

    All functionality of :class:`h5py.File` is preserved (for details
    see http://docs.h5py.org/en/latest/)
    """

    def __init__(
        self,
        name: str,
        mode="r",
        control_path="/",
        digitizer_path="/",
        msi_path="/",
        silent=False,
        **kwargs
    ):
        """
        :param name: name (and path) of file on disk
        :param mode: readonly :code:`'r'` (DEFAULT) and read/write
            :code:`'r+'`
        :param control_path: internal HDF5 path to group containing
            control devices
        :param digitizer_path: internal HDF5 path to group containing
            digitizer devices
        :param msi_path: internal HDF5 path to group containing MSI
            devices
        :param silent: set :code:`True` to suppress warnings
            (:code:`False` DEFAULT)
        :param kwargs:  additional keywords passed on to
            :class:`h5py.File`

        :Example:

            >>> # open HDF5 file
            >>> f = File('sample.hdf5',
            ...          control_path='Raw data + config',
            ...          digitizer_path='Raw data + config',
            ...          msi_path='MSI')
            >>> type(f)
            bapsflib._hdf.utils.file.File
        """
        # initialize
        if mode not in ("r", "r+"):
            raise ValueError(
                "Only `mode` readonly 'r' and read/write 'r+' are supported."
            )
        kwargs["mode"] = mode
        h5py.File.__init__(self, name, **kwargs)

        # -- define device paths --
        #: Internal HDF5 path for control devices. (DEFAULT :code:`'/'`)
        self.CONTROL_PATH = control_path

        #: Internal HDF5 path for digitizer devices.
        #: (DEFAULT :code:`'/'`)
        self.DIGITIZER_PATH = digitizer_path

        #: Internal HDF5 path for MSI devices. (DEFAULT :code:`'/'`)
        self.MSI_PATH = msi_path

        # -- map and build info --
        warn_filter = "ignore" if silent else "default"
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter)

            # create map
            self._map_file()

            # build `_info` attribute
            self._build_info()

    def _build_info(self):
        """Builds the general :attr:`info` dictionary for the file."""
        # define file keys
        self._info = {
            "file": os.path.basename(self.filename),
            "absolute file path": os.path.abspath(self.filename),
        }

    def _map_file(self):
        """Map/re-map the HDF5 file. (Builds :attr:`file_map`)"""
        self._file_map = HDFMap(
            self,
            control_path=self.CONTROL_PATH,
            digitizer_path=self.DIGITIZER_PATH,
            msi_path=self.MSI_PATH,
        )

    @property
    def controls(self) -> HDFMapControls:
        """Dictionary of control device mappings."""
        return self.file_map.controls

    @property
    def digitizers(self) -> HDFMapDigitizers:
        """Dictionary of digitizer device mappings"""
        return self.file_map.digitizers

    @property
    def file_map(self) -> HDFMap:
        """HDF5 file map (:class:`~bapsflib._hdf.maps.core.HDFMap`)"""
        return self._file_map

    @property
    def info(self) -> Dict[str, Any]:
        """
        Dictionary of general info on the HDF5 file and the experimental
        run.
        """
        return self._info

    @property
    def msi(self) -> HDFMapMSI:
        """Dictionary of MSI device mappings."""
        return self.file_map.msi

    @property
    def overview(self):
        """
        HDF5 file overview. (:class:`~.hdfoverview.HDFOverview`)
        """
        # to avoid cyclical imports
        from bapsflib._hdf.utils.hdfoverview import HDFOverview

        return HDFOverview(self)

    def read_controls(
        self,
        controls: List[Union[str, Tuple[str, Any]]],
        shotnum=slice(None),
        intersection_set=True,
        silent=False,
        **kwargs
    ):
        """
        Reads data from control device datasets.  See
        :class:`~.hdfreadcontrols.HDFReadControls` for more detail.

        :param controls:

            A list of strings and/or 2-element tuples
            indicating the control device(s).  If a control device has
            only one configuration then only the device name
            :code:`'control'` needs to be passed in the list.  If a
            control device has multiple configurations, then the device
            name and its configuration "name" needs to be passed as a
            tuple element :code:`('control', 'config')` in the list.
            (see :func:`~.helpers.condition_controls` for details)

        :type controls: List[Union[str, Tuple[str, Any]]]
        :param shotnum:

            HDF5 file shot number(s) indicating data entries to be
            extracted

        :type shotnum: Union[int, list(int), slice(), numpy.array]
        :param bool intersection_set:

            :code:`True` (DEFAULT) will force the returned shot numbers
            to be the intersection of :data:`shotnum` and the shot
            numbers contained in each control device dataset.
            :code:`False` will return the union instead of the
            intersection, minus :math:`shotnum \\le 0`. (see
            :class:`~.hdfreadcontrols.HDFReadControls`
            for details)

        :param bool silent:

            :code:`False` (DEFAULT).  Set :code:`True` to ignore any
            UserWarnings (soft-warnings)

        :rtype: :class:`~.hdfreadcontrols.HDFReadControls`

        :Example:

            >>> # open HDF5 file
            >>> f = File('sample.hdf5')
            >>>
            >>> # list control devices
            >>> list(f.controls)
            ['6K Compumotor', 'Waveform']
            >>>
            >>> # list '6K Compumotor' configurations
            >>> list(f.controls['6K Compumotor'].configs)
            [2, 3]
            >>>
            >>> # extract all '6k Compumotor' data for configuration 3
            >>> cdata = f.read_controls([('6K Compumotor', 3)])
            >>> type(cdata)
            bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls
            >>>
            >>> # list 'Waveform' configurations
            >>> list(f.file_map.controls['Waveform'].configs)
            ['config01']
            >>>
            >>> # extract 'Waveform' data
            >>> cdata = f.read_controls(['Waveform'])
            >>> list(cdata.info['controls'])
            ['Waveform']
            >>>
            >>> # extract both 'Waveform' and '6K Compumotor'
            >>> controls = ['Waveform', ('6K Compumotor', 2)]
            >>> cdata = f.read_controls(controls)
            >>> list(cdata.info['controls'])
            ['6K Compumotor', 'Waveform']

        """
        # to avoid cyclical imports
        from bapsflib._hdf.utils.hdfreadcontrols import HDFReadControls

        warn_filter = "ignore" if silent else "default"
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter)
            data = HDFReadControls(
                self,
                controls,
                shotnum=shotnum,
                intersection_set=intersection_set,
                **kwargs
            )

        return data

    def read_data(
        self,
        board: int,
        channel: int,
        index=slice(None),
        shotnum=slice(None),
        digitizer=None,
        adc=None,
        config_name=None,
        keep_bits=False,
        add_controls=None,
        intersection_set=True,
        silent=False,
        **kwargs
    ):
        """
        Reads data from digitizer datasets and attaches control device
        data when requested. (see :class:`.hdfreaddata.HDFReadData`
        for details)

        :param board: digitizer board number
        :param channel: digitizer channel number
        :param index: dataset row index
        :type index: Union[int, list(int), slice(), numpy.array]
        :param shotnum: HDF5 global shot number
        :type shotnum: Union[int, list(int), slice(), numpy.array]
        :param str digitizer: name of digitizer
        :param str adc: name of the digitizer's analog-digital converter
        :param str config_name: name of digitizer configuration
        :param bool keep_bits:

            :code:`True` to keep digitizer signal in bits,
            :code:`False` (default) to convert digitizer signal to
            voltage

        :param add_controls:

            A list of strings and/or 2-element tuples
            indicating the control device(s).  If a control device has
            only one configuration then only the device name
            :code:`'control'` needs to be passed in the list.  If a
            control device has multiple configurations, then the device
            name and its configuration "name" needs to be passed as a
            tuple element :code:`('control', 'config')` in the list.
            (see :func:`~.helpers.condition_controls` for details)

        :type add_controls: List[Union[str, Tuple[str, Any]]]
        :param bool intersection_set:

            :code:`True` (DEFAULT) will force the returned shot numbers
            to be the intersection of :data:`shotnum`, the digitizer
            dataset shot numbers, and, if requested, the shot numbers
            contained in  each control device dataset. :code:`False`
            will return the union instead of the intersection, minus
            :math:`shotnum \le 0`. (see
            :class:`~.hdfreaddata.HDFReadData` for details)

        :param bool silent:

            :code:`False` (DEFAULT).  Set :code:`True` to ignore any
            UserWarnings (soft-warnings)

        :rtype: :class:`~.hdfreaddata.HDFReadData`

        :Example:

            >>> # open HDF5 file
            >>> f = File('sample.hdf5')
            >>>
            >>> # list control devices
            >>> list(f.digitizers)
            ['SIS crate']
            >>>
            >>> # get active configurations
            >>> f.digitizers['SIS crate'].configs
            ['config01', 'config02']
            >>>
            >>> # get active adc's for config
            >>> f.digitizers['SIS crate'].configs['config01']['adc']
            ('SIS 3302,)
            >>>
            >>> # get first connected brd and channels to adc
            >>> brd, chs = f.digitizers['SIS crate'].configs['config01'][
            ...     'SIS 3302'][0][0:2]
            >>> brd
            1
            >>> chs
            (1, 2, 3)
            >>>
            >>> # get data for brd = 1, ch = 1
            >>> data = f.read_data(brd, chs[0],
            ...                    digitizer='SIS crate',
            ...                    adc='SIS 3302',
            ...                    config_name='config01')
            >>> type(data)
            bapsflib._hdf.utils.hdfreaddata.HDFReadData
            >>>
            >>> # Note: a quicker way to see how the digitizers are
            >>> #       configured is to use
            >>> #
            >>> #       f.overview.report_digitizers()
            >>> #
            >>> #       which prints to screen a report of the
            >>> #       digitizer hookup
        """
        # to avoid cyclical imports
        from bapsflib._hdf.utils.hdfreaddata import HDFReadData

        warn_filter = "ignore" if silent else "default"
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter)
            data = HDFReadData(
                self,
                board,
                channel,
                index=index,
                shotnum=shotnum,
                digitizer=digitizer,
                adc=adc,
                config_name=config_name,
                keep_bits=keep_bits,
                add_controls=add_controls,
                intersection_set=intersection_set,
                **kwargs
            )

        return data

    def read_msi(self, msi_diag: str, silent=False, **kwargs):
        """
        Reads data from MSI Diagnostic datasets.  See
        :class:`~.hdfreadmsi.HDFReadMSI` for more detail.

        :param msi_diag: name of MSI diagnostic
        :param bool silent:

            :code:`False` (DEFAULT).  Set :code:`True` to ignore any
            UserWarnings (soft-warnings)

        :rtype: :class:`~.hdfreadmsi.HDFReadMSI`

        :Example:

            >>> # open HDF5 file
            >>> f = File('sample.hdf5')
            >>>
            >>> # list msi diagnostics
            >>> list(f.msi)
            ['Interferometer array', 'Magnetic field']
            >>>
            >>> # read 'Interferometer array'
            >>> mdata = f.read_msi('Interferometer array')
            >>> type(mdata)
            bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI
        """
        from bapsflib._hdf.utils.hdfreadmsi import HDFReadMSI

        warn_filter = "ignore" if silent else "default"
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter)
            data = HDFReadMSI(self, msi_diag, **kwargs)

        return data
