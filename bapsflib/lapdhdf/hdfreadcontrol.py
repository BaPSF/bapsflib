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


class hdfReadControl(np.recarray):
    """
    Extracts control device data from the HDF5 file.
    """
    # .. note::
    #
    #     It is assumed that control data is always extracted with the
    #    intent of being matched to digitizer data
    #
    # Extracting Data:
    # - if multiple controls are specified then,
    #   ~ only one control of each contype can be in the list of
    #     controls
    #   ~ if a specified control does not exist in the HDF5 file, then
    #     it will be deleted from the specified 'controls' list
    #   ~ the returned structured array will only contain intersecting
    #     HDF5 shot numbers (i.e. shot numbers that are included in
    #     all specified control datasets)
    #   ~ then, those intersecting shot numbers are filtered according
    #     to the index and shotnum keywords
    #
    def __new__(cls, hdf_file, controls,
                shotnum=slice(None), intersection_set=True,
                silent=False, **kwargs):
        """
        :param hdf_file: object instance of the HDF5 file
        :type hdf_file: :class:`bapsflib.lapdhdf.files.File`
        :param controls: a list indicating the desired control devices
            (see
            :func:`bapsflib.lapdhdf.hdfreadcontrol.condition_controls`
            for details)
        :type controls: [str, (str, val), ]
        :param shotnum: HDF5 file shot number(s) indicating data
            entries to be extracted (:code:`shotnum` will take
            precedence over :code:`index`)
        :type shotnum: :code:`None`, int, list(int), or
            slice(start, stop, step)
        :param bool intersection_set:
        :param bool silent:

        Behavior of :data:`shotnum`
            * indexing starts at 1
            * if :code:`intersection_set=True`, then only data
              corresponding to shot numbers that are specified in
              shotnum and are in all control datasets will be returned
            * if :code:`intersection_set=False`, then the returned array
              will have entries for all shot numbers specified in
              shotnum but entries that do not correlate with data in
              control datasets will be give null values.
        """
        # When inheriting from numpy, the object creation and
        # initialization is handled by __new__ instead of __init__.
        #
        # param control:
        # - control is a string list naming the control to be read out
        # - if a control contains multiple devices, then it's entry in
        #   the control list must be a 2-element tuple where the 1st
        #   element is the control name and the 2nd element is a unique
        #   specifier.
        #   e.g. the '6K Compumotor' can have multiple probe drives
        #   which are identified by their receptacle number, so
        #
        #       controls = [('6K Compumotor', 1),]
        #
        #   would indicate a readout of receptacle 1 of the
        #   '6K Compumotor'
        # - The list can only contain one entry from each contype. i.e.
        #   This is valid:
        #
        #       controls = ['6K Compumotor', 'Waveform', 'N5700_PS']
        #
        #   but this is not:
        #
        #       controls = ['6K Compumotor', 'NI_XZ']
        #

        # initialize timing
        if 'timeit' in kwargs:
            timeit = kwargs['timeit']
            if timeit:
                tt = [time.time()]
            else:
                timeit = False
        else:
            timeit = False

        # initiate warning string
        warn_str = ''

        # ---- Condition hdf_file ----
        # Check hdf_file is a lapdhdf.File object
        try:
            file_map = hdf_file.file_map
        except AttributeError:
            raise AttributeError(
                "hdf_file needs to be of type lapdhdf.File")

        # Check for non-empty controls
        if not file_map.controls or file_map.controls is None:
            raise ValueError(
                'There are no control devices in the HDF5 file.')

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - hdf_file conditioning: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # ---- Condition 'controls' Argument ----
        # condition elements of 'controls' argument
        # - Controls is a list where elements can be:
        #   1. a string indicating the name of a control device
        #   2. a 2-element tuple where the 1st entry is a string
        #      indicating the name of a control device and the 2nd is
        #      a unique specifier for that control device
        # - there can only be one control device per contype
        # - some calling routines (such as, lapdhdf.File.read_data)
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
        if timeit:
            tt.append(time.time())
            print('tt - condition controls: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # ---- Condition shotnum ----
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
            # control name and unique specifier
            cname = control[0]
            cspec = control[1]

            # gather control datasets
            # TODO: determine shotnumkey through cmap.configs
            #       - i.e. scan
            #         cmap.configs[cspec]['dset field to numpy field']
            #         for numpy field 'shotnum' and grab the associated
            #         dset field
            #
            cmap = file_map.controls[cname]
            cdset_name = cmap.construct_dataset_name(cspec)
            cdset_path = cmap.info['group path'] + '/' + cdset_name
            cdset_dict[cname] = hdf_file.get(cdset_path)
            shotnumkey_dict[cname] = cdset_dict[cname].dtype.names[0]

        # Catch shotnum if a slice object or int
        # - For either case, convert shotnum to a list
        #
        if type(shotnum) is slice:
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

                # add to first_sn
                first_sn.append(start)
            if intersection_set:
                start = max(first_sn)

            # re-define shotnum as a list
            shotnum = np.arange(start, stop, step).tolist()
        elif type(shotnum) is int:
            shotnum = [shotnum]
        elif type(shotnum) is not list:
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
            # control name and unique specifier
            cname = control[0]
            cspec = control[1]
            cmap = file_map.controls[cname]

            # get a conditioned version of index, shotnum, and sni for
            # each control
            index_dict[cname], shotnum_dict[cname], sni_dict[cname] = \
                condition_shotnum_list(shotnum, cdset_dict[cname],
                                       shotnumkey_dict[cname],
                                       cmap, cspec)

        # convert shotnum from list to np.array
        shotnum = np.array(shotnum)
        if len(shotnum.shape) != 1:
            shotnum = shotnum.squeeze()
        # shotnum = np.array([shotnum]) if type(shotnum) is int \
        #     else np.array(shotnum)

        # re-filter index, shotnum, sni
        if intersection_set:
            shotnum, shotnum_dict, sni_dict, index_dict = \
                do_shotnum_intersection(shotnum,
                                        shotnum_dict,
                                        sni_dict,
                                        index_dict)

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - condition shotnum: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # ---- Build obj ----
        # Determine fields for numpy array
        # npfields - dictionary of structured array field names
        #            npfields['field name'] = [type, shape]
        #
        npfields = {}
        for control in controls:
            # control name and unique specifier
            cname = control[0]
            cspec = control[1]

            # gather fields
            cmap = file_map.controls[cname]
            for df_name, nf_name, npi \
                    in cmap.configs[cspec]['dset field to numpy field']:
                # df_name - control dataset field name
                #           ~ if a tuple instead of a string then the
                #             dataset field is linked to a command list
                # nf_name - numpy structured array field name and dtype
                # npi     - numpy index df_name will be inserted into
                if nf_name[0] == 'shotnum':
                    # already in dtype
                    pass
                elif nf_name[0] in npfields:
                    npfields[nf_name[0]][1] += 1
                else:
                    npfields[nf_name[0]] = [nf_name[1], 1]
                    # npfields[nf_name] = ['<f8, 1]

        # Define dtype and shape for numpy array
        dtype = [('shotnum', '<u4', 1)]
        for key in npfields:
            dtype.append((key, npfields[key][0], npfields[key][1]))
        shape = shotnum.shape

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - define dtype: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # Initialize Control Data
        data = np.empty(shape, dtype=dtype)
        data['shotnum'] = shotnum.view()

        # TODO: this should be done in the main array fill section
        # for field in npfields:
        #    if data.dtype[field] <= np.int:
        #        data[field][:] = -99999
        #    elif data.dtype[field] <= np.float:
        #        data[field][:] = np.nan

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - initialize data np.ndarray: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # Assign Control Data to Numpy array
        for control in controls:
            # control name and unique specifier
            cname = control[0]
            cspec = control[1]

            # get control dataset
            cmap = file_map.controls[cname]
            cdset = cdset_dict[cname]
            shotnumkey = shotnumkey_dict[cname]
            sni = sni_dict[cname]
            index = index_dict[cname]
            if type(index) is np.ndarray:
                index = index.tolist()

            # populate control data array
            if intersection_set:
                # find cdset indices that match shotnum
                # - Note: if the control device utilizes one dataset for
                #         all configurations, then 'shoti' will contain
                #         indices for all the configurations.  This will
                #         need to be filtered again for the wanted
                #         configuration.
                #
                # shoti = np.in1d(cdset[shotnumkey], shotnum)

                # assign values
                # df_name - device dataset field name
                # nf_name - corresponding numpy field name and dtype
                # npi     - numpy index that dataset will be assigned to
                #
                for df_name, nf_name, npi \
                        in cmap.configs[cspec][
                            'dset field to numpy field']:
                    # skip iteration if field is 'shotnum'
                    if nf_name[0] == 'shotnum':
                        continue

                    # assign data
                    # TODO: need to confirm this works for all cl setups
                    if cmap.has_command_list:
                        # get command list
                        cl = cmap.configs[cspec]['command list']

                        # retrieve array of command indices
                        ci_arr = cdset[index, df_name].view()

                        # assign command values to data
                        for ci, command in enumerate(cl):
                            ii = np.where(ci_arr == ci, True, False)
                            data[nf_name[0]][ii] = command
                    else:
                        # control does NOT use command list
                        if data.dtype[nf_name[0]].shape != ():
                            # for fields that contain arrays
                            # (e.g. 'xyz')
                            data[nf_name[0]][:, npi] = \
                                cdset[index, df_name].view()
                        else:
                            # for fields that contain a constant
                            data[nf_name[0]] = \
                                cdset[index, df_name].view()
            else:
                # TODO: need to confirm this works
                # get intersecting shot numbers
                # sn_intersect - shot numbers that are common between
                #                shotnum and the control dataset
                # cdseti - a bool array matching the size of the control
                #          dataset and labeling True for for control
                #          dataset array shot numbers that are in the
                #          shotnum
                # NOTE: cdseti will have to be filtered again for
                #       control devices that utilize one dataset for
                #       multiple configurations. They will need to be
                #       filtered for the desired configuration.
                #
                # sn_intersect = np.intersect1d(cdset[shotnumkey],
                #                               shotnum).view()
                # cdseti = np.in1d(cdset[shotnumkey], sn_intersect)

                # assign values
                # df_name - device dataset field name
                # nf_name - corresponding numpy field name and dtype
                # npi     - numpy index that dataset will be assigned to
                #
                for df_name, nf_name, npi \
                        in cmap.configs[cspec][
                            'dset field to numpy field']:
                    # skip iteration if field is 'shotnum'
                    if nf_name[0] == 'shotnum':
                        continue

                    # assign data
                    if cmap.has_command_list:
                        # get command list
                        cl = cmap.configs[cspec]['command list']

                        # retrieve array of command indices
                        ci_arr = cdset[index, df_name].view()

                        # NaN fill data
                        # TODO: this will need to be modified for dtype
                        data[nf_name[0]].fill('')

                        # assign command values to data
                        # 1. find where command index (ci) is in the
                        #    command index array (ci_arr)
                        # 2. ci_arr.size == index.size
                        # 3. ii.size == ci_arr.size
                        # 4. sni.size != index.size
                        # 5. np.where(sni)[0].size == index.size
                        #
                        for ci, command in enumerate(cl):
                            # find command index (ci) locations in
                            # command index array (ci_arr)
                            # - ii is a boolean mask
                            # - ii.size == ci_arr.size == index.size
                            #
                            ii = np.where(ci_arr == ci, True, False)

                            # need a re-filtered sni for this specific
                            # ci
                            #
                            sni_for_ci = np.zeros(sni.shape, dtype=bool)
                            sni_for_ci[np.where(sni)[0][ii]] = True

                            # assign value
                            data[nf_name[0]][sni_for_ci] = command
                    else:
                        # control does NOT use command list
                        # overhead for NaN filling
                        sni_not = np.logical_not(sni)
                        fname = nf_name[0]

                        # begin data assignment
                        if data.dtype[fname].shape != ():
                            # for fields that contain arrays
                            # (e.g. 'xyz')
                            data[fname][sni, npi] = \
                                cdset[index, df_name].view()

                            # NaN fill
                            dtype = data.dtype[fname].base
                            if np.issubdtype(dtype, np.integer):
                                data[fname][sni_not, npi] = -99999
                            elif np.issubdtype(dtype, np.floating):
                                data[fname][sni_not, npi] = np.nan
                            elif np.issubdtype(dtype, np.flexible):
                                data[fname][sni_not, npi] = ''
                        else:
                            # for fields that contain a constant
                            data[fname][sni] = \
                                cdset[index, df_name].view()

                            # NaN fill
                            dtype = data.dtype[fname].base
                            if np.issubdtype(dtype, np.integer):
                                data[fname][sni_not] = -99999
                            elif np.issubdtype(dtype, np.floating):
                                data[fname][sni_not] = np.nan
                            elif np.issubdtype(dtype, np.flexible):
                                data[fname][sni_not] = ''
                    '''
                    try:
                        # control uses a command list
                        #
                        # get command list
                        cl = cmap.configs[cspec]['command list']

                        # filter 'datai' and 'cdseti' for values only
                        # associated with cspec
                        #
                        if len(cmap.dataset_names) == 1 \
                                and len(cmap.configs) != 1:
                            # multiple configs but one dataset...need
                            # to filter

                            # get config field
                            cfield = None
                            for field in cmap.configs['dataset fields']:
                                if 'configuration' \
                                        in field[0].casefold():
                                    cfield = field[0]
                                    break

                            # get indices for data corresponding to
                            # cspec
                            try:
                                cfi = np.where(cdset[cfield] == cspec)
                            except ValueError:
                                raise ValueError(
                                    'control device dataset has NO '
                                    'identifiable configuration field')

                            # filter 'cdseti'
                            cdseti = np.logical_and(cdseti, cfi)

                        # retrieve array of command indices
                        ci_arr = cdset[cdseti, df_name].view()

                        # retrieve shot number array for dataset
                        sn_arr = cdset[cdseti, shotnumkey].view()

                        for ci, command in enumerate(cl):
                            ii = np.where(ci_arr == ci, True, False)
                            datai = np.in1d(shotnum, sn_arr[ii])
                            data[nf_name[0]][datai] = command

                    except KeyError:
                        # oops control does NOT use command list
                        #
                        # get matching data array shot number indices
                        datai = np.in1d(shotnum, sn_intersect)

                        # fill data array
                        if data.dtype[nf_name[0]].shape != ():
                            data[nf_name[0]][datai, npi] = \
                                cdset[cdseti, df_name].view()
                        else:
                            data[nf_name[0]][datai] = \
                                cdset[cdseti, df_name].view()
                    '''

            # print execution timing
            if timeit:
                tt.append(time.time())
                print('tt - fill data - '
                      + '{}: '.format(cname)
                      + '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # print execution timing
        if timeit:
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
        if timeit:
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

    # def __init__(self, *args, **kwargs):
    #     super().__init__()


def condition_controls(hdf_file, controls, **kwargs):

    # Check hdf_file is a lapdhdf.File object
    try:
        file_map = hdf_file.file_map
    except AttributeError:
        raise AttributeError(
            "hdf_file needs to be of type lapdhdf.File")

    # Check for non-empty controls
    if not file_map.controls or file_map.controls is None:
        raise AttributeError('There are no control devices in the HDF5'
                             ' file.')

    # condition elements of 'controls' argument
    # - controls is a list where elements can be:
    #   1. a string indicating the name of a control device
    #   2. a 2-element tuple where the 1st entry is a string
    #      indicating the name of a control device and the 2nd is
    #      a unique specifier for that control device
    #      ~ in 0.1.3.dev3 the unique specifier is the name used in
    #        configs['config names']
    #
    # - ensure
    #   1. controls is in agreement is defined format above
    #   2. all control device are in file_map.controls
    #   3. there are not duplicate devices in controls
    #   4. proper unique specifiers are defined
    #
    if type(controls) is list:
        # catch an empty list
        if len(controls) == 0:
            raise ValueError('controls argument empty')

        # all list items have to be strings or tuples
        if not all([True if isinstance(con, (str, tuple)) else False
                    for con in controls]):
            raise TypeError('controls argument invalid')

        # condition controls
        new_controls = []
        for device in controls:
            if type(device) is str:
                # ensure proper device and unique specifier are defined
                if device in new_controls:
                    raise TypeError(
                        'Control device ({})'.format(device)
                        + ' can only have one occurrence in controls')
                elif device in file_map.controls:
                    if len(file_map.controls[device].configs) == 1:
                        new_controls.append((
                            device,
                            list(file_map.controls[device].configs)[0]
                        ))
                    else:
                        raise TypeError(
                            'Need to define a unique specifier for '
                            'control device ({})'.format(device))
                else:
                    raise TypeError(
                        'Control device ({})'.format(device)
                        + ' not in HDF5 file')
            elif type(device) is tuple:
                if device[0] in new_controls:
                    raise TypeError(
                        'Control device ({})'.format(device[0])
                        + ' can only have one occurrence in controls')
                elif device[0] in file_map.controls:
                    if device[1] in file_map.controls[
                            device[0]].configs:
                        new_controls.append((device[0], device[1]))
                    else:
                        raise TypeError(
                            'Unique specifier for control device '
                            '({}) is NOT valid'.format(device[0]))
                else:
                    raise TypeError(
                        'Control device ({})'.format(device[0])
                        + ' not in HDF5 file')
    else:
        raise TypeError('controls argument not a list')

    # enforce one device per contype
    checked = []
    controls = new_controls
    for device in controls:
        # device is a tuple, not a string
        contype = file_map.controls[device[0]].contype

        if contype in checked:
            raise TypeError('controls has multiple devices per contype')
        else:
            checked.append(contype)

    # return conditioned list
    return controls


def gather_shotnums(hdf_file, controls, method='union',
                    assume_controls_conditioned=False):

    # condition controls
    if not assume_controls_conditioned:
        controls = condition_controls(hdf_file, controls)

    # condition 'method' keyword
    if method not in ['union', 'intersection', 'first']:
        raise TypeError("Keyword 'method' can only be one of "
                        "{}".format(['union',
                                     'intersection',
                                     'first']))

    # build array of shot numbers
    shotnumarr = None
    for device in controls:
        # control name and unique specifier
        try:
            if type(device) is str:
                raise TypeError('controls NOT conditioned')

            # get device name (cname) and unique specifier (cspec)
            cname = device[0]
            cspec = device[1]
        except IndexError:
            raise TypeError('controls NOT conditioned')

        # get control dataset
        conmap = hdf_file.file_map.controls[cname]
        cdset_name = conmap.construct_dataset_name(cspec)
        cdset_path = conmap.info['group path'] + '/' + cdset_name
        cdset = hdf_file.get(cdset_path)
        shotnumkey = cdset.dtype.names[0]

        # get filter indices for cspec of cname
        # - a control device that utilizes a 'command list' saves all of
        #   its data for all of its configurations in one dataset
        # - in this case, the dataset needs to be filtered for data only
        #   corresponding to the cspec configuration
        #
        if len(conmap.dataset_names) == 1 and len(conmap.configs) != 1:
            # multiple configs but one dataset

            # get configuration field
            cfield = None
            for field in conmap.configs['dataset fields']:
                if 'configuration' in field[0].casefold():
                    cfield = field[0]
                    break

            # get indices for data corresponding to cspec
            try:
                cfi = np.where(cdset[cfield] == cspec)
            except ValueError:
                raise ValueError(
                    'control device dataset has NO identifiable '
                    'configuration field')
        else:
            cfi = np.ones(cdset.shape, dtype=bool)

        # Define shotnumarr
        if shotnumarr is None:
            # first assignment
            shotnumarr = cdset[cfi, shotnumkey].view()

            # break if only want shot numbers for first dataset
            if method == 'first':
                break
        elif method == 'intersection':
            # build set of intersecting shot numbers
            shotnumarr = np.intersect1d(shotnumarr,
                                        cdset[cfi, shotnumkey].view(),
                                        assume_unique=True)
        else:
            # method == 'union'
            shotnumarr = np.union1d(shotnumarr,
                                    cdset[cfi, shotnumkey].view())

    # return numpy array of intersecting shot numbers
    return shotnumarr


# rename to condition_shotnum
def condition_shotnum_list(shotnum, cdset, shotnumkey, cmap, cspec):
    """
    Conditions **shotnum** (when a `list`) against the control dataset
    **cdset**.  Utilizes functions :func:`condition_shotnum_list_simple`
    and :func:`condition_shotnum_list_complex`.

    :param shotnum: desired HDF5 shot number
    :type shotnum: list(int)
    :param cdset: control device dataset
    :type cdset: :class:`h5py.Dataset`
    :param str shotnumkey: field name in the control device dataset that
        contains the shot numbers
    :param cmap: mapping object for control device
    :param cspec: unique specifier (configuration name) for the control
        device
    :return: index, shotnum, sni

    .. note::

        The returned :class:`numpy.ndarray`'s (:const:`index`,
        :const:`shotnum`, and :const:`sni`) follow the rule::

            shotnum[sni] = cdset[index, shotnumkey]
    """
    # Inputs:
    # shotnum    (list(int))    - the desired shot number
    # cdset      (h5py.Dataset) - the control dataset
    # shotnumkey (str)          - field name for the shot number column
    #                             in cdset
    # cmap                      - file mapping object for the control
    #                             device
    # cspec                     - unique specifier (aka configuration
    #                             name) for control device
    #
    # Returns:
    # index    np.array(dtype=uint32) - cdset row index for the
    #                                   specified shotnum
    # shotnum  np.array(dtype=uint32) - shot numbers
    # sni      np.array(dtype=bool)   - shotnum mask such that:
    #            shotnum[sni] = cdset[index, shotnumkey]
    #
    # Initialize come vars
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
                                           cmap, cspec)

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
                                   cspec):
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
    :param cspec: unique specifier (configuration name) for the control
        device
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
    for df in cmap.configs[cspec]['dataset fields']:
        if 'configuration' in df[0].casefold():
            configkey = df[0]
            break
    if configkey == '':
        raise ValueError(
            'Can NOT find configuration field in the control'
            + ' ({}) dataset'.format(cmap.name))

    # find index
    if cdset.shape[0] == n_configs:
        # only one possible shotnum, index can be 0 to n_configs-1
        #
        # NOTE: The HDF5 configuration field stores a string with the
        #       name of the configuration.  When reading that into a
        #       numpy array the string becomes a byte string (i.e. b'').
        #       When comparing with np.where() the comparing string
        #       needs to be encoded (i.e. cspec.encode()).
        #
        only_sn = cdset[0, shotnumkey]
        sni = np.where(shotnum == only_sn, True, False)

        # construct index
        if True not in sni:
            # shotnum does not contain only_sn
            index = np.empty(shape=0, dtype=np.uint32)
        else:
            config_name_arr = cdset[0:n_configs, configkey]
            index = np.where(config_name_arr == cspec.encode())[0]

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
        config_where = np.where(config_name_arr == cspec.encode())[0]
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
