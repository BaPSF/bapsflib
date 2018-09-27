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
import numpy as np
import time

from functools import reduce
from warnings import warn


class HDFReadControl(np.recarray):
    """
    Reads control device data from the HDF5 file.

    .. note::

        * It is assumed that control data is always extracted with the
          intent of being matched to digitizer data.
        * Only one control for each :const:`contype` can be specified
          at a time.
        * It is assumed that there is only ONE dataset associated with
          each control device.
    """
    #
    # Extracting Data:
    # - if multiple controls are specified then,
    #   ~ only one control of each contype can be in the list of
    #     controls
    #   ~ if a specified control does not exist in the HDF5 file, then
    #     a TypeError will be raised
    #   ~ if a control device configuration is not specified, then if
    #     the control has one config then that config will be assumed,
    #     otherwise, a TypeError will be raised
    #
    warn("attribute access to numpy array fields will be deprecated "
         "by Oct., access fields like data['shotnum'] NOT like "
         "data.shotnum",
         FutureWarning)

    def __new__(cls, hdf_file, controls,
                shotnum=slice(None), intersection_set=True,
                silent=False, **kwargs):
        """
        :param hdf_file: object instance of the HDF5 file
        :type hdf_file: :class:`bapsflib.lapd.files.File`
        :param controls: a list indicating the desired control devices
            (see
            :func:`bapsflib.lapd.hdfreadcontrol.condition_controls`
            for details)
        :type controls: [str, (str, val), ]
        :param shotnum: HDF5 file shot number(s) indicating data
            entries to be extracted
        :type shotnum: int, list(int), or slice(start, stop, step)
        :param bool intersection_set: :code:`True` (DEFAULT) will force
            the returned shot numbers to be the intersection of
            :data:`shotnum` and the shot numbers contained in each
            control device dataset. :code:`False` will return the union
            instead of the intersection
        :param bool silent: :code:`False` (DEFAULT).  Set :code:`True`
            to suppress command line printout of soft-warnings

        Behavior of :data:`shotnum` and :data:`intersection_set`:
            * :data:`shotnum` indexing starts at 1
            * any values :code:`<= 0` will be thrown out
            * if :code:`intersection_set=True`, then only data
              corresponding to shot numbers that are specified in
              shotnum and are in all control datasets will be returned
            * if :code:`intersection_set=False`, then the returned array
              will have entries for all shot numbers specified in
              shotnum but entries that do not correlate with shot
              numbers in control datasets will be give null values of
              :code:`-99999`, :code:`numpy.nan`, or :code:`''`,
              depending on :code:`numpy.dtype`.
        """
        # When inheriting from numpy, the object creation and
        # initialization is handled by __new__ instead of __init__.
        #
        # :param: controls:
        # - :data:`controls` is a list of strings or 2-element tuples
        # - if an element is a string
        #   * that string is the name of the desired control device
        #   * the control device must have only one configuration
        # - if an element is a 2-element tuple:
        #   * the 1st value is a string naming the control device
        #   * the 2nd value is the device configuration name as defined
        #     in the device mapping
        # - :data:`controls` can only contain one control device for
        #   each :data:`contype`
        # - Examples:
        #   1. a '6K Compumotor' with multiple configurations
        #
        #       controls = [('6K Compumotor', 1)]
        #
        #   2. a '6K Compumotor' with multiple configurations and a
        #      'Waveform' with one configuration
        #
        #       controls = ['Waveform, ('6K Compumotor', 1)]
        #

        # initialize timing
        tt = []
        if 'timeit' in kwargs:  # pragma: no cover
            timeit = kwargs['timeit']
            if timeit:
                tt.append(time.time())
            else:
                timeit = False
        else:
            timeit = False

        # initiate warning string
        warn_str = ''

        # ---- Condition `hdf_file`                                 ----
        # - `hdf_file` is a lapd.file object
        #
        if not isinstance(hdf_file, bapsflib.lapd.File):
            raise TypeError(
                '`hdf_file` is NOT type `bapsflib.lapd.File`')

        # grab instance of _fmap
        _fmap = hdf_file.file_map

        # Check for non-empty controls
        # if not _fmap.controls or _fmap.controls is None:
        if not bool(_fmap.controls):
            raise ValueError(
                'There are no control devices in the HDF5 file.')

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print('tt - hdf_file conditioning: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # ---- Condition 'controls' Argument ----
        # - some calling routines (such as, lapd.File.read_data)
        #   already properly condition 'controls', so passing a keyword
        #   'assume_controls_conditioned' allows for a bypass of
        #   conditioning here
        #
        try:
            if not kwargs['assume_controls_conditioned']:
                controls = condition_controls(hdf_file, controls,
                                              silent=silent)
        except KeyError:
            controls = condition_controls(hdf_file, controls,
                                          silent=silent)

        # make sure 'controls' is not empty
        if not controls:
            raise ValueError("improper 'controls' arg passed")

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print('tt - condition controls: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # ---- Condition shotnum ----
        # TODO: REVIEW THIS COMMENT BLOCK
        # shotnum -- global HDF5 file shot number
        #            ~ this is the index used to link values between
        #              datasets
        #
        # Through conditioning the following are (re-)defined:
        # index   -- row index of control dataset(s)
        #            ~ if len(controls) = 1, then will be an int or a
        #              list(int), or list(list(int))
        #            ~ if len(controls) > 1, then will be a
        #              list(list(int)) where len(index) = len(controls)
        # shotnum -- global HDF5 shot number
        #            ~ index at 1
        #            ~ will be a filtered version of input kwarg shotnum
        #              based on intersection_set
        #            ~ converted to np.ndarray(dtype=uint32,
        #                                      shape=(sn_size,))
        # sni     -- bool array for providing a one-to-one mapping
        #            between shotnum[sni] and index
        #            ~ np.ndarray(dtype=bool,
        #                         shape=(nControls, sn_size))
        #            ~ cdata['shotnum'][sni] = shtonum[sni]
        #                                    = cdset[index, shotnumkey]
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
        #         specified by shotnum
        #       > if a dataset does not included a shot number contained
        #         in shotnum, then its entry in the returned array will
        #         be given a numpy.nan value
        #
        # dset_sn - 1D array of shotnum's that will be either the
        #           intersection of shot numbers of all control device
        #           datasets specified by controls (for
        #           intersection_set=True) or the shot numbers of the
        #           first control device dataset specified in controls
        #           (for intersection_set=False)
        # shotnum - regardless of if index or shotnum is specified,
        #           shotnum will be re-defined to include all shot
        #           numbers that will be placed into the obj array
        #
        # Determine dset_sn and rowlen
        # method = 'intersection' if intersection_set else 'first'
        # dset_sn = gather_shotnums(hdf_file, controls, method=method,
        #                           assume_controls_conditioned=True)

        # Grab control datasets
        #
        cdset_dict = {}
        shotnumkey_dict = {}
        for control in controls:
            # control name (cname) and configuration name (cconfn)
            cname = control[0]
            cconfn = control[1]

            # gather control datasets and shotnumkey's
            cmap = _fmap.controls[cname]
            cdset_path = cmap.configs[cconfn]['dset paths'][0]
            cdset_dict[cname] = hdf_file.get(cdset_path)
            try:
                shotnumkey = \
                    cmap.configs[cconfn]['shotnum']['dset field'][0]
                shotnumkey_dict[cname] = shotnumkey
            except KeyError:
                raise ValueError(
                    'no shot number field defined for control device')

        # Catch shotnum if a slice object or int
        # - For either case, convert shotnum to a list
        #
        if isinstance(shotnum, slice):
            # Here convert slice to list
            #
            # determine largest possible shot number
            last_sn = [
                cdset_dict[cname][-1, shotnumkey_dict[cname]] + 1
                for cname in cdset_dict
            ]
            if shotnum.stop is not None:
                last_sn.append(shotnum.stop)
            stop_sn = max(last_sn)

            # get the start, stop, and step for the shot number array
            start, stop, step = shotnum.indices(stop_sn)

            # determine smallest possible shot number
            # - intersection_set = True
            #   * start = max of first_sn and shotnum.start
            # - intersection_set = False
            #   * start = min of first_sn and shotnum.start
            first_sn = [cdset_dict[cname][0, shotnumkey_dict[cname]]
                        for cname in cdset_dict]
            if shotnum.start is not None:
                # ensure shot numbers are >= 1
                if start <= 0:
                    start = 1
            else:
                # start wasn't specified in slice object
                start = min(first_sn)

            # adjust start for intersection_set
            if intersection_set:
                first_sn.append(start)
                start = max(first_sn)

            # re-define shotnum as a list
            shotnum = np.arange(start, stop, step).tolist()
        elif isinstance(shotnum, int):
            # Here convert int to list
            shotnum = [shotnum]
        elif not isinstance(shotnum, list):
            raise ValueError('Valid shotnum not passed')
        else:
            # shotnum is a list
            # ensure all elements are int
            if not all(isinstance(sn, int) for sn in shotnum):
                raise ValueError('Valid shotnum not passed')

        # Ensure 'shotnum' is valid
        # - at this point 'shotnum' should be a list
        # - after this block (by the time you get to
        #   ---- Build obj ----) 'shotnum' will be converted to a numpy
        #   1D array containing the shot numbers to be included in the
        #   returned obj array
        #
        # Notes:
        # 1. shotnum can not be converted to a np.array until after
        #    shotnum, index, and sni are determined for each control
        # 2. all entries in shotnum_dict, index_dict, and sni_dict
        #    should be np.arrays
        # 3. shotnum values used to fill shotnum_dict should not go
        #    through an intersection filtering in here, this will be
        #    done after this for-loop
        #
        index_dict = {}
        shotnum_dict = {}
        sni_dict = {}
        for control in controls:
            # control name (cname) and configuration name (cconfn)
            cname = control[0]
            cconfn = control[1]
            cmap = _fmap.controls[cname]

            # get a conditioned version of index, shotnum, and sni for
            # each control
            index_dict[cname], shotnum_dict[cname], sni_dict[cname] = \
                condition_shotnum(shotnum, cdset_dict[cname],
                                  shotnumkey_dict[cname],
                                  cmap, cconfn)

        # convert shotnum from list to np.array
        shotnum = np.array(shotnum)
        if len(shotnum.shape) != 1:
            shotnum = shotnum.squeeze()

        # re-filter index, shotnum, sni
        if intersection_set:
            shotnum, shotnum_dict, sni_dict, index_dict = \
                do_shotnum_intersection(shotnum,
                                        shotnum_dict,
                                        sni_dict,
                                        index_dict)

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print('tt - condition shotnum: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # ---- Build obj ----
        # Define dtype and shape for numpy array
        shape = shotnum.shape
        dtype = [('shotnum', '<u4', 1)]
        for control in controls:
            # control name (cname) and configuration name (cconfn)
            cname = control[0]
            cconfn = control[1]

            # add fields
            cconfig = _fmap.controls[cname].configs[cconfn]
            for field_name, fconfig in \
                    cconfig['state values'].items():
                dtype.append((
                    field_name,
                    fconfig['dtype'],
                    fconfig['shape']
                ))

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print('tt - define dtype: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # Initialize Control Data
        data = np.empty(shape, dtype=dtype)
        data['shotnum'] = shotnum.view()

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print('tt - initialize data np.ndarray: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # Assign Control Data to Numpy array
        for control in controls:
            # control name (cname) and configuraiton name (cconfn)
            cname = control[0]
            cconfn = control[1]

            # get control dataset
            cmap = _fmap.controls[cname]
            cconfig = cmap.configs[cconfn]
            cdset = cdset_dict[cname]
            sni = sni_dict[cname]
            index = index_dict[cname]
            if isinstance(index, np.ndarray):
                index = index.tolist()

            # populate control data array
            # 1. scan over numpy fields
            # 2. scan over the dset fields that will fill the numpy
            #    fields
            # 3. split between a command list fill or a direct fill
            # 4. NaN fill if intersection_set = False
            #
            for nf_name, fconfig \
                    in cconfig['state values'].items():
                # nf_name
                #   the numpy field name
                # fconfig
                #   the mapping dictionary for nf_name
                for npi, df_name in enumerate(fconfig['dset field']):
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
                        cl = fconfig['command list']

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
                        if data.dtype[nf_name].shape != ():
                            # field contains an array (e.g. 'xyz')
                            data[nf_name][sni, npi] = \
                                cdset[index, df_name].view()
                        else:
                            # field is a constant
                            data[nf_name][sni] = \
                                cdset[index, df_name].view()

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
                        if np.issubdtype(dtype, np.integer):
                            # any integer, signed or not
                            data[nf_name][ii] = -99999
                        elif np.issubdtype(dtype, np.floating):
                            # any float type
                            data[nf_name][ii] = np.nan
                        elif np.issubdtype(dtype, np.flexible):
                            # string, unicode, void
                            data[nf_name][ii] = ''
                        else:
                            # no real NaN concept exists
                            # - this shouldn't happen though
                            warn('dtype ({}) of '.format(dtype)
                                 + '{} has no Nan '.format(nf_name)
                                 + 'concept...no NaN fill done')

            # print execution timing
            if timeit:  # pragma: no cover
                tt.append(time.time())
                print('tt - fill data - '
                      + '{}: '.format(cname)
                      + '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # print execution timing
        if timeit:  # pragma: no cover
            n_controls = len(controls)
            tt.append(time.time())
            print('tt - fill data array: '
                  '{} ms'.format((tt[-1] - tt[-n_controls-2]) * 1.E3)
                  + ' (intersection_set={})'.format(intersection_set))

        # Construct obj
        obj = data.view(cls)

        # assign dataset info
        # TODO: add a dict key for each control w/ controls config
        # - control configs dict should include:
        #   ~ 'contype'
        #   ~ 'dataset name'
        #   ~ 'dataset path'
        #
        obj.info = {
            'hdf file': hdf_file.filename.split('/')[-1],
            'controls': controls,
            'probe name': None,
            'port': (None, None)}

        # populate meta-info from controls.configs
        # TODO: populate info from controls.configs
        #

        # print warnings
        if not silent and warn_str != '':
            print(warn_str)

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print('tt - total execution time: '
                  '{} ms'.format((tt[-1] - tt[0]) * 1.E3))

        # return obj
        return obj

    def __array_finalize__(self, obj):
        # according to numpy documentation:
        #  __array__finalize__(self, obj) is called whenever the system
        #  internally allocates a new array from obj, where obj is a
        #  subclass (subtype) of the (big)ndarray. It can be used to
        #  change attributes of self after construction (so as to ensure
        #  a 2-d matrix for example), or to update meta-information from
        #  the parent. Subclasses inherit a default implementation of
        #  this method that does nothing.
        if obj is None:
            return

        # Define info attribute
        # - getattr() searches obj for the 'info' attribute. If the
        #   attribute exists, then it's returned. If the attribute does
        #   NOT exist, then the 3rd arg is returned as a default value.
        self.info = getattr(obj, 'info',
                            {'hdf file': None,
                             'controls': None,
                             'probe name': None,
                             'port': (None, None)})


def condition_controls(hdf_file: bapsflib.lapd.File,
                       controls,
                       **kwargs) -> List[Tuple[str, Any]]:
    """
    Conditions the `controls` argument for :class:`HDFReadControl`.

    :param hdf_file: HDF5 object instance
    :param controls: `controls` argument to be conditioned
    :return: list containing tuple pairs of control control name and
        desired configuration name

    :Example:

        >>> from bapsflib import lapd
        >>> f = lapd.File('sample.hdf5')
        >>> controls = ['Wavefrom', ('6K Compumotor', 3)]
        >>> condition = condition_controls(f, controls)
        >>> condition
        [('Waveform', 'config01'), ('6K Compumotor', 3)]

    """
    # grab instance of file mapping
    _fmap = hdf_file.file_map

    # -- condition 'controls' argument                              ----
    # - controls is:
    #   1. a string or Iterable
    #   2. each element is either a string or tuple
    #   3. if tuple, then length <= 2
    #      ('control name',) or ('control_name', config_name)
    #
    # check if NULL
    if not bool(controls):
        # catch a null controls
        raise ValueError('controls argument is NULL')

    # make string a list
    if isinstance(controls, str):
        controls = [controls]

    # condition Iterable
    if isinstance(controls, Iterable):
        # all list items have to be strings or tuples
        if not all(isinstance(con, (str, tuple)) for con in controls):
            raise TypeError('all elements of `controls` must be of '
                            'type string or tuple')

        # condition controls
        new_controls = []
        for control in controls:
            if isinstance(control, str):
                name = control
                config_name = None
            else:
                # tuple case
                if len(control) > 2:
                    raise ValueError(
                        "a `controls` tuple element must be specified "
                        "as ('control name') or, "
                        "('control name', config_name)")

                name = control[0]
                config_name = None if len(control) == 1 else control[1]

            # ensure proper control and unique specifier are defined
            if name in [cc[0] for cc in new_controls]:
                raise ValueError(
                    'Control device ({})'.format(control)
                    + ' can only have one occurrence in controls')
            elif name in _fmap.controls:
                if config_name in _fmap.controls[name].configs:
                    # all is good
                    pass
                elif len(_fmap.controls[name].configs) == 1 \
                        and config_name is None:
                    config_name = list(_fmap.controls[name].configs)[0]
                else:
                    raise ValueError(
                        "'{}' is not a valid ".format(config_name)
                        + "configuration name for control device "
                        + "'{}'".format(name))
            else:
                raise ValueError('Control device ({})'.format(name)
                                 + ' not in HDF5 file')

            # add control to new_controls
            new_controls.append((name, config_name))
    else:
        raise TypeError('`controls` argument is not Iterable')

    # enforce one control per contype
    checked = []
    controls = new_controls
    for control in controls:
        # control is a tuple, not a string
        contype = _fmap.controls[control[0]].contype

        if contype in checked:
            raise TypeError('`controls` has multiple devices per '
                            'contype')
        else:
            checked.append(contype)

    # return conditioned list
    return controls


def condition_shotnum(
        shotnum: Any,
        cdset: h5py.Dataset,
        shotnumkey: str,
        cmap: ControlMap,
        cconfn: Any) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Conditions **shotnum** (when a `list`) against the control dataset
    **cdset**.  Utilizes functions :func:`condition_shotnum_list_simple`
    and :func:`condition_shotnum_list_complex`.

    :param shotnum: desired HDF5 shot number(s)
    :type shotnum: list(int)
    :param cdset: control device dataset
    :type cdset: :class:`h5py.Dataset`
    :param str shotnumkey: field name in the control device dataset that
        contains the shot numbers
    :param cmap: mapping object for control device
    :param cconfn: configuration name for the control device
    :return: index, shotnum, sni

    .. note::

        The returned :class:`numpy.ndarray`'s (:const:`index`,
        :const:`shotnum`, and :const:`sni`) follow the rule::

            shotnum[sni] = cdset[index, shotnumkey]
    """
    # Inputs:
    # shotnum    (list(int))    - the desired shot number(s)
    # cdset      (h5py.Dataset) - the control dataset
    # shotnumkey (str)          - field name for the shot number column
    #                             in cdset
    # cmap                      - file mapping object for the control
    #                             device
    # cconfn                    - configuration for control device
    #
    # Returns:
    # index    np.array(dtype=uint32) - cdset row index for the
    #                                   specified shotnum
    # shotnum  np.array(dtype=uint32) - shot numbers
    # sni      np.array(dtype=bool)   - shotnum mask such that:
    #            shotnum[sni] = cdset[index, shotnumkey]
    #
    # Initialize some vars
    n_configs = len(cmap.configs)
    configs_per_row = 1 if cmap.one_config_per_dset else n_configs

    # remove shot numbers less-than or equal to 0
    shotnum.sort()
    shotnum = list(set(shotnum))
    shotnum.sort()
    if min(shotnum) <= 0:
        # remove values less-than or equal to 0
        new_sn = [sn for sn in shotnum if sn > 0]
        shotnum = new_sn

    # ensure shotnum is not empty
    if len(shotnum) == 0:
        raise ValueError('Valid shotnum not passed.')

    # convert shotnum to np.array
    # - shotnum is always a list up to this point
    shotnum = np.array(shotnum).view()

    # Calc. index, shotnum, and sni
    if configs_per_row == 1:
        # the dataset only saves data for one configuration
        index, shotnum, sni = \
            condition_shotnum_list_simple(shotnum, cdset, shotnumkey)
    else:
        # the dataset saves data for multiple configurations
        index, shotnum, sni = \
            condition_shotnum_list_complex(shotnum, cdset, shotnumkey,
                                           cmap, cconfn)

    # return calculated arrays
    return index.view(), shotnum.view(), sni.view()


# rename to condition_shotnum_w_simple_dset
def condition_shotnum_list_simple(shotnum, cdset, shotnumkey):
    """
    Conditions **shotnum** (when a `list`) against control dataset
    **cdset** when the control dataset contains recorded data for
    ONLY ONE device configuration.

    :param shotnum: desired HDF5 shot number
    :type shotnum: :class:`numpy.ndarray`
    :param cdset: control device dataset
    :type cdset: :class:`h5py.Dataset`
    :param str shotnumkey: field name in the control device dataset that
        contains the shot numbers
    :return: index, shotnum, sni

    .. note::

        The returned :class:`numpy.ndarray`'s (:const:`index`,
        :const:`shotnum`, and :const:`sni`) follow the rule::

            shotnum[sni] = cdset[index, shotnumkey]
    """
    # this is for a dataset that only records data for one configuration
    #
    # get corresponding indices for shotnum
    # build associated sni array
    #
    if cdset.shape[0] == 1:
        # only one possible shot number
        only_sn = cdset[0, shotnumkey]
        sni = np.where(shotnum == only_sn, True, False)
        index = np.array([0]) \
            if True in sni else np.empty(shape=0, dtype=np.uint32)
    else:
        # get 1st and last shot number
        first_sn, last_sn = cdset[[-1, 0], shotnumkey]

        if last_sn - first_sn + 1 == cdset.shape[0]:
            # shot numbers are sequential
            index = shotnum - first_sn

            # build sni and filter index
            sni = np.where(index < cdset.shape[0], True, False)
            index = index[sni]
        else:
            # shot numbers are NOT sequential
            step_front_read = shotnum[-1] - first_sn
            step_end_read = last_sn - shotnum[0]

            if cdset.shape[0] <= 1 + min(step_front_read,
                                         step_end_read):
                # cdset.shape is smaller than the theoretical reads from
                # either end of the array
                #
                cdset_sn = cdset[shotnumkey].view()
                sni = np.isin(shotnum, cdset_sn)

                # define index
                index = np.where(np.isin(cdset_sn, shotnum))[0]
            elif step_front_read <= step_end_read:
                # extracting from the beginning of the array is the
                # smallest
                some_cdset_sn = cdset[0:step_front_read + 1, shotnumkey]
                sni = np.isin(shotnum, some_cdset_sn)

                # define index
                index = np.where(np.isin(some_cdset_sn, shotnum))[0]
            else:
                # extracting from the end of the array is the smallest
                start, stop, step = slice(-step_end_read - 1,
                                          None,
                                          None).indices(cdset.shape[0])
                some_cdset_sn = cdset[start::, shotnumkey]
                sni = np.isin(shotnum, some_cdset_sn)

                # define index
                # NOTE: if index is empty (i.e. index.shape[0] == 0)
                #       then adding an int still returns an empty array
                index = np.where(np.isin(some_cdset_sn, shotnum))[0]
                index += start

    # return calculated arrays
    return index.view(), shotnum.view(), sni.view()


# rename to condition_shotnum_w_complex_dset
def condition_shotnum_list_complex(shotnum, cdset, shotnumkey, cmap,
                                   cconfn):
    """
    Conditions **shotnum** (when a `list`) against control dataset
    **cdset** when the control dataset contains recorded data for
    multiple device configurations.

    .. admonition:: Dataset Assumption

        There is an assumption that each shot number spans **n_configs**
        number of rows in the dataset, where **n_configs** is the number
        of control device configurations.  It is also assumed that the
        order in which the configs are recorded is the same for each
        shot number.  That is, if there are 3 configs (config01,
        config02, and config03) and the first three rows of the dataset
        are recorded in that order, then each following grouping of
        three rows will maintain that order.

    :param shotnum: desired HDF5 shot number
    :type shotnum: :class:`numpy.ndarray`
    :param cdset: control device dataset
    :type cdset: :class:`h5py.Dataset`
    :param str shotnumkey: field name in the control device dataset that
        contains the shot numbers
    :param cmap: mapping object for control device
    :param cconfn: configuration name for the control device
    :return: index, shotnum, sni

    .. note::

        The returned :class:`numpy.ndarray`'s (:const:`index`,
        :const:`shotnum`, and :const:`sni`) follow the rule::

            shotnum[sni] = cdset[index, shotnumkey]
    """
    # this is for a dataset that only records data for one configuration
    #
    # Ensure there is only one dataset for all configs
    # Note: we should only get to this point if n_dsets != n_configs
    n_dsets = len(cmap.dataset_names)
    n_configs = len(cmap.configs)
    if n_dsets != 1:
        raise ValueError(
            'Control has {} datasets and'.format(n_dsets)
            + ' {} configurations, do NOT'.format(n_configs)
            + ' know how to handle')

    # determine configkey
    # - configkey is the dataset field name for the column that contains
    #   the associated configuration name
    #
    configkey = ''
    for df in cdset.dtype.names:
        if 'configuration' in df.casefold():
            configkey = df
            break
    if configkey == '':
        raise ValueError(
            'Can NOT find configuration field in the control'
            + ' ({}) dataset'.format(cmap.device_name))

    # find index
    if cdset.shape[0] == n_configs:
        # only one possible shotnum, index can be 0 to n_configs-1
        #
        # NOTE: The HDF5 configuration field stores a string with the
        #       name of the configuration.  When reading that into a
        #       numpy array the string becomes a byte string (i.e. b'').
        #       When comparing with np.where() the comparing string
        #       needs to be encoded (i.e. cconfn.encode()).
        #
        only_sn = cdset[0, shotnumkey]
        sni = np.where(shotnum == only_sn, True, False)

        # construct index
        if True not in sni:
            # shotnum does not contain only_sn
            index = np.empty(shape=0, dtype=np.uint32)
        else:
            config_name_arr = cdset[0:n_configs, configkey]
            index = np.where(config_name_arr == cconfn.encode())[0]

            if index.size != 1:
                # something went wrong...no configurations are found
                # and, thus, the routines assumption's do not match
                # the format of the dataset
                raise ValueError
    else:
        # get 1st and last shot number
        first_sn, last_sn = cdset[[-1, 0], shotnumkey]

        # find sub-group index corresponding to the requested device
        # configuration
        config_name_arr = cdset[0:n_configs, configkey]
        config_where = np.where(config_name_arr == cconfn.encode())[0]
        if config_where.size == 1:
            config_subindex = config_where[0]
        else:
            # something went wrong...either no configurations
            # are found or the routine's assumptions do not
            # match the format of the dataset
            raise ValueError

        # construct index for remaining scenarios
        if n_configs * (last_sn - first_sn + 1) == cdset.shape[0]:
            # shot numbers are sequential and there are n_configs per
            # shot number
            index = shotnum - first_sn

            # adjust index to correspond to associated configuration
            # - stretch by n_configs then shift by config_subindex
            #
            index = (n_configs * index) + config_subindex

            # build sni and filter index
            sni = np.where(index < cdset.shape[0], True, False)
            index = index[sni]
        else:
            # shot numbers are NOT sequential
            step_front_read = shotnum[-1] - first_sn
            step_end_read = last_sn - shotnum[0]

            # construct index and sni
            if cdset.shape[0] <= n_configs * (
                    min(step_front_read, step_end_read) + 1):
                # cdset.shape is smaller than the theoretical
                # sequential array
                cdset_sn = cdset[config_subindex::n_configs,
                                 shotnumkey].view()
                sni = np.isin(shotnum, cdset_sn)
                index = np.where(np.isin(cdset_sn, shotnum))[0]

                # adjust index to correspond to associated configuration
                index = (config_subindex + 1) * index
            elif step_front_read <= step_end_read:
                # extracting from the beginning of the array is the
                # smallest
                start = config_subindex
                stop = n_configs * (step_front_read + 1)
                stop += config_subindex
                step = n_configs
                some_cdset_sn = cdset[start:stop:step,
                                      shotnumkey].view()
                sni = np.isin(shotnum, some_cdset_sn)
                index = np.where(np.isin(some_cdset_sn, shotnum))[0]

                # adjust index to correspond to associated configuration
                index = (config_subindex + 1) * index
            else:
                # extracting from the end of the array is the
                # smallest
                start, stop, step = \
                    slice(-n_configs * (step_end_read + 1),
                          None,
                          n_configs).indices(cdset.shape[0])
                start += config_subindex
                some_cdset_sn = cdset[start:stop:step,
                                      shotnumkey].view()
                sni = np.isin(shotnum, some_cdset_sn)
                index = np.where(np.isin(some_cdset_sn, shotnum))

                # adjust index to correspond to associated configuration
                index = (config_subindex + 1) * index
                index += start

    # return calculated arrays
    return index.view(), shotnum.view(), sni.view()


def do_shotnum_intersection(shotnum, shotnum_dict, sni_dict, index_dict):
    # determine intersecting shot numbers
    # - I'm assuming no intersection as been performed yet
    #
    sn_list = [shotnum_dict[key][sni_dict[key]]
               for key in shotnum_dict]
    sn_list.append(shotnum)
    shotnum_intersect = reduce(
        lambda x, y: np.intersect1d(x, y, assume_unique=True),
        sn_list)
    if shotnum_intersect.shape[0] == 0:
        raise ValueError(
            'Input shotnum would result in a null array')
    else:
        shotnum = shotnum_intersect

    # now filter
    for cname in shotnum_dict:
        new_sn_mask = np.isin(
            shotnum_dict[cname][sni_dict[cname]], shotnum)
        new_sn = \
            shotnum_dict[cname][sni_dict[cname]][new_sn_mask]
        new_index = index_dict[cname][new_sn_mask]
        shotnum_dict[cname] = new_sn
        index_dict[cname] = new_index
        sni_dict[cname] = np.ones(new_index.shape[0],
                                  dtype=bool)

    return shotnum, shotnum_dict, sni_dict, index_dict
