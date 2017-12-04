# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#

import h5py
import numpy as np
import time

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
                index=None, shotnum=None, intersection_set=True,
                silent=False, **kwargs):
        """
        :param hdf_file: object instance of the HDF5 file
        :type hdf_file: :class:`bapsflib.lapdhdf.files.File`
        :param controls: a list indicating the desired control devices
            (see
            :func:`bapsflib.lapdhdf.hdfreadcontrol.condition_controls`
            for details)
        :type controls: [str, (str, val), ]
        :param index: row index (see 'index behavior below')
        :type index: :code:`None`, int, list(int), or
            slice(start, stop, step)
        :param shotnum: HDF5 file shot number(s) indicating data
            entries to be extracted (:code:`shotnum` will take
            precedence over :code:`index`)
        :type shotnum: :code:`None`, int, list(int), or
            slice(start, stop, step)
        :param bool intersection_set:
        :param bool silent:

        Behavior of :data:`index`
            * indexing starts at 0
            * is overridden by :data:`shotnum`
            * if :code:`intersection_set=True`
                * If :code:`len(controls) == 1`, then :data:`index` will
                  be the dataset row index.
                * If :code:`len(controls) > 1`, then :data:`index` will
                  correspond to the index of the list of intersecting
                  shot numbers of all specified control devices.
            * if :code:`intersection_set=False`
                * :data:`index` corresponds to the row index of the
                  dataset for the first control device listed in
                  :data:`controls`.

        Behavior of :data:`shotnum`
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

        # ---- Condition index and shotnum Keywords ----
        # index   -- row index of dataset
        #            ~ indexed at 0
        #            ~ overridden by shotnum
        # shotnum -- global HDF5 file shot number
        #            ~ this is the index used to link values between
        #              datasets
        #            ~ supersedes any other indexing keyword
        #
        # - Indexing behavior: (depends on intersection_set)
        #
        #   ~ intersection_set = True
        #     * index
        #       > if len(controls) == 1, then index will be the dataset
        #         row index
        #       > if len(controls) > 1, then index will correspond to
        #         the index of the list of intersecting shot numbers of
        #         all specified control devices
        #     * shotnum
        #       > the returned array will only contain shot numbers that
        #         are in the intersection of shotnum and all the
        #         specified control device datasets
        #
        #   ~ intersection_set = False
        #     * index
        #       > index corresponds to the 1st dataset row index
        #       > if the 2nd and later datasets don't include the
        #         shotnum of the 1st dataset, then they will be given a
        #         numpy.nan value
        #     * shotnum
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
        method = 'intersection' if intersection_set else 'first'
        dset_sn = gather_shotnums(hdf_file, controls, method=method,
                                  assume_controls_conditioned=True)
        rowlen = dset_sn.shape[0]

        # Ensure 'index' is a valid
        # - Valid index types are: None, int, list(int), and slice()
        #     None      => extract all indices
        #     int       => extract shot with index int
        #     list(int) => extract shots with indices specified in list
        #     slice(start, stop, skip)
        #               = > same as [start:stop:skip]
        #
        # if index is None:
        #     index = slice(None, None, None)
        #
        if shotnum is not None:
            # ignore index keyword if shotnum is used
            index = None
        elif index is None:
            # default to shotnum keyword
            pass
        elif type(index) is int:
            if not (index in range(rowlen)
                    or -index - 1 in range(rowlen)):
                raise ValueError(
                    'index is not in range({})'.format(rowlen))
        elif type(index) is list:
            # all elements need to be integers
            if all(type(s) is int for s in index):
                # condition list
                index.sort()
                index = list(set(index))
                newindex = []
                for s in index:
                    if s < 0:
                        s = -s - 1
                    if s in range(rowlen):
                        if s not in newindex:
                            newindex.append(s)
                    else:
                        warn_str += (
                            '\n** Warning: shot {} not a '.format(s)
                            + 'valid index, range({})'.format(rowlen))
                newindex.sort()

                if len(newindex) != 0:
                    index = newindex
                else:
                    raise ValueError('index: none of the elements are '
                                     'in range({})'.format(rowlen))
            else:
                raise ValueError("index keyword needs to be None, int, "
                                 "list(int), or slice object")
        elif type(index) is slice:
            # valid type
            pass
        else:
            raise ValueError("index keyword needs to be None, int, "
                             "list(int), or slice object")

        # Ensure 'shotnum' is valid
        # - here 'shotnum' will be converted from its keyword type to a
        #   1D array containing the list of shot numbers to be included
        #   in the returned obj array
        #
        if index is not None:
            # - index conditioning should ensure index is not None only
            #   if shotnum is not specified (i.e. shotnum is None and
            #   index is not None)
            #
            shotnum = dset_sn[index].view()
            if type(shotnum) is np.int32:
                shotnum = np.array([shotnum]).view()
        elif shotnum is None:
            # assume all intersecting entries are desired
            shotnum = dset_sn.view()
        elif type(shotnum) is int:
            if shotnum in dset_sn:
                shotnum = np.array([shotnum])
            else:
                raise ValueError('shotnum [{}] is not '.format(shotnum)
                                 + 'a valid shot number')
        elif type(shotnum) is list:
            # shotnum's have to be ints and >=1
            if all(type(s) is int for s in shotnum):
                # remove shot numbers less-than or equal to 0
                shotnum.sort()
                shotnum = list(set(shotnum))
                try:
                    zindex = shotnum.index(0)
                    del shotnum[:zindex+1]
                except ValueError:
                    # no values less-than or equal to 0
                    pass

                # convert shotnum to np.array
                if intersection_set:
                    shotnum = np.intersect1d(shotnum, dset_sn).view()
                else:
                    shotnum = np.array(shotnum).view()

                # ensure obj will not be a zero dim array
                if shotnum.shape[0] == 0:
                    raise ValueError('Valid shotnum not passed')
            else:
                raise ValueError('Valid shotnum not passed')
        elif type(shotnum) is slice:
            try:
                if shotnum.start <= 0 or shotnum.stop <= 0:
                    raise ValueError('Valid shotnum not passed')
            except TypeError:
                if shotnum.stop is None:
                    raise ValueError('Valid shotnum not passed')
                elif shotnum.start is None:
                    shotnum = slice(shotnum.stop-1, shotnum.stop,
                                    shotnum.step)

            # convert shotnum to np.array
            if intersection_set:
                shotnum = np.intersect1d(
                    np.arange(shotnum.start,
                              shotnum.stop,
                              shotnum.step),
                    dset_sn).view()
            else:
                shotnum = np.arange(shotnum.start, shotnum.stop,
                                    shotnum.step)

            # ensure obj will not be a zero dim array
            if shotnum.shape[0] == 0:
                raise ValueError('Valid shotnum not passed')
        else:
            raise ValueError('Valid shotnum not passed')

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
                # nf_name - numpy structured array field name
                # npi     - numpy index df_name will be inserted into
                if nf_name == 'shotnum':
                    # already in dtype
                    pass
                elif nf_name in npfields:
                    npfields[nf_name][1] += 1
                else:
                    npfields[nf_name] = ['<f8', 1]

        # Define dtype and shape for numpy array
        dytpe = [('shotnum', '<u4', 1)]
        for key in npfields:
            dytpe.append((key, npfields[key][0], npfields[key][1]))
        shape = shotnum.shape

        # Initialize Control Data
        data = np.empty(shape, dtype=dytpe)
        data['shotnum'] = shotnum.view()
        for field in npfields:
            if data.dtype[field] <= np.int:
                data[field][:] = -99999
            else:
                data[field][:] = np.nan

        # Assign Control Data to Numpy array
        for control in controls:
            # control name and unique specifier
            cname = control[0]
            cspec = control[1]

            # get control dataset
            cmap = file_map.controls[cname]
            cdset_name = cmap.construct_dataset_name(cspec)
            cdset_path = cmap.info['group path'] + '/' + cdset_name
            cdset = hdf_file.get(cdset_path)
            shotnumkey = cdset.dtype.names[0]

            # populate control data array
            if intersection_set:
                # find cdset indices that match shotnum
                shoti = np.in1d(cdset[shotnumkey], shotnum)

                # assign values
                # df_name - device dataset field name
                #           ~ if a tuple instead of a string then the
                #             dataset field is linked to a command list
                # nf_name - corresponding numpy field name
                # npi     - numpy index that dataset will be assigned to
                #
                for df_name, nf_name, npi \
                        in cmap.configs[cspec][
                            'dset field to numpy field']:
                    # skip iteration if field is 'shotnum'
                    if nf_name == 'shotnum':
                        continue

                    # assign data
                    # TODO: filling from command list type
                    try:
                        # control uses a command list
                        #
                        # get command list
                        cl = cmap.configs[cspec]['command list']
                    except KeyError:
                        # oops control does NOT use command list
                        if data.dtype[nf_name].shape != ():
                            data[nf_name][:, npi] = \
                                cdset[shoti, df_name].view()
                        else:
                            data[nf_name] = \
                                cdset[shoti, df_name].view()
            else:
                # get intersecting shot numbers
                sn_intersect = np.intersect1d(cdset[shotnumkey],
                                              shotnum).view()
                datai = np.in1d(shotnum, sn_intersect)
                cdseti = np.in1d(cdset[shotnumkey], sn_intersect)

                # assign values
                # df_name - device dataset field name
                # nf_name - corresponding numpy field name
                # npi     - numpy index that dataset will be assigned to
                #
                for df_name, nf_name, npi \
                        in cmap.configs[cspec][
                            'dset field to numpy field']:
                    # skip iteration if field is 'shotnum'
                    if nf_name == 'shotnum':
                        continue

                    # assign data
                    try:
                        # control uses a command list
                        #
                        # get command list
                        cl = cmap.configs[cspec]['command list']
                    except KeyError:
                        # oops control does NOT use command list
                        if data.dtype[nf_name].shape != ():
                            data[nf_name][datai, npi] = \
                                cdset[df_name][cdseti].view()
                        else:
                            data[nf_name][datai] = \
                                cdset[df_name][cdseti].view()

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

        # print warnings
        if not silent and warn_str != '':
            print(warn_str)

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

    def __init__(self, *args, **kwargs):
        super().__init__()


def condition_controls(hdf_file, controls, silent=False):

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
