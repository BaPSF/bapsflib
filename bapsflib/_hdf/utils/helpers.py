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
Helper functions that are utilized by the the HDF5 utility classes
defined in module :mod:`bapsflib._hdf.utils`.
"""
__all__ = [
    "build_shotnum_dset_relation",
    "build_sndr_for_simple_dset",
    "build_sndr_for_complex_dset",
    "condition_controls",
    "condition_shotnum",
    "do_shotnum_intersection",
]

import h5py
import numpy as np

from typing import Any, Dict, Iterable, List, Tuple, Union

from bapsflib._hdf.maps.controls.templates import (
    HDFMapControlCLTemplate,
    HDFMapControlTemplate,
)
from bapsflib._hdf.utils.file import File

# define type aliases
ControlMap = Union[HDFMapControlTemplate, HDFMapControlCLTemplate]
IndexDict = Dict[str, np.ndarray]


def build_shotnum_dset_relation(
    shotnum: np.ndarray,
    dset: h5py.Dataset,
    shotnumkey: str,
    cmap: ControlMap,
    cconfn: Any,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compares the **shotnum** numpy array to the specified dataset,
    **dset**, to determine which indices contain the desired shot
    number(s)
    [for :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`].
    As a results, two numpy arrays are returned which satisfy the rule::

        shotnum[sni] = dset[index, shotnumkey]

    where **shotnum** is the original shot number array, **sni** is a
    boolean numpy array masking which shot numbers were determined to
    be in the dataset, and **index** is an array of indices
    corresponding to the desired shot number(s).

    :param shotnum: desired HDF5 shot number(s)
    :param dset: control device dataset
    :type dset: :class:`h5py.Dataset`
    :param str shotnumkey: field name in the control device dataset that
        contains shot numbers
    :param cmap: mapping object for control device
    :param cconfn: configuration name for the control device
    :return: :code:`index` and :code:`sni` numpy arrays

    .. note::

        This function leverages the functions
        :func:`~.helpers.build_sndr_for_simple_dset`
        and
        :func:`~.helpers.build_sndr_for_complex_dset`
    """
    # Inputs:
    # shotnum      - the desired shot number(s)
    # dset         - the control device dataset
    # shotnumkey   - field name for the shot number column in dset
    # cmap         - file mapping object for the control device
    # cconfn       - configuration for control device
    #
    # Returns:
    # index     np.array(dtype=uint32)  - dset row index for the
    #                                     specified shotnum
    # shotnum   np.array(dtype=uint32)  - shot numbers
    # sni       np.array(dtype=bool)    - shotnum mask such that:
    #
    #            shotnum[sni] = dset[index, shotnumkey]
    #
    # Calc. index, shotnum, and sni
    if cmap.one_config_per_dset:
        # the dataset only saves data for one configuration
        index, sni = build_sndr_for_simple_dset(shotnum, dset, shotnumkey)
    else:
        # the dataset saves data for multiple configurations
        index, sni = build_sndr_for_complex_dset(shotnum, dset, shotnumkey, cmap, cconfn)

    # return calculated arrays
    return index.view(), sni.view()


def build_sndr_for_simple_dset(
    shotnum: np.ndarray, dset: h5py.Dataset, shotnumkey: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compares the **shotnum** numpy array to the specified "simple"
    dataset, **dset**, to determine which indices contain the desired
    shot number(s).  As a results, two numpy arrays are returned which
    satisfy the rule::

        shotnum[sni] = dset[index, shotnumkey]

    where **shotnum** is the original shot number array, **sni** is a
    boolean numpy array masking which shot numbers were determined to
    be in the dataset, and **index** is an array of indices
    corresponding to the desired shot number(s).

    A "simple" dataset is a dataset in which the data for only ONE
    configuration is recorded.

    :param shotnum: desired HDF5 shot number
    :param dset: dataset containing shot numbers
    :type dset: :class:`h5py.Dataset`
    :param str shotnumkey: field name in the dataset that contains
        the shot numbers
    :return: :code:`index` and :code:`sni` numpy arrays
    """
    # this is for a dataset that only records data for one configuration
    #
    # get corresponding indices for shotnum
    # build associated sni array
    #
    if dset.shape[0] == 1:
        # only one possible shot number
        only_sn = dset[0, shotnumkey]
        sni = np.where(shotnum == only_sn, True, False)
        index = np.array([0]) if True in sni else np.empty(shape=0, dtype=np.uint32)
    else:
        # get 1st and last shot number
        first_sn = dset[0, shotnumkey]
        last_sn = dset[-1, shotnumkey]

        if last_sn - first_sn + 1 == dset.shape[0]:
            # shot numbers are sequential
            index = shotnum - first_sn

            # build sni and filter index
            sni = np.where(index < dset.shape[0], True, False)
            index = index[sni]
        else:
            # shot numbers are NOT sequential
            step_front_read = shotnum[-1] - first_sn
            step_end_read = last_sn - shotnum[0]

            if dset.shape[0] <= 1 + min(step_front_read, step_end_read):
                # dset.shape is smaller than the theoretical reads from
                # either end of the array
                #
                dset_sn = dset[shotnumkey].view()
                sni = np.isin(shotnum, dset_sn)

                # define index
                index = np.where(np.isin(dset_sn, shotnum))[0]
            elif step_front_read <= step_end_read:
                # extracting from the beginning of the array is the
                # smallest
                some_dset_sn = dset[0 : step_front_read + 1, shotnumkey]
                sni = np.isin(shotnum, some_dset_sn)

                # define index
                index = np.where(np.isin(some_dset_sn, shotnum))[0]
            else:
                # extracting from the end of the array is the smallest
                start, stop, step = slice(
                    -step_end_read.astype(np.int32) - 1, None, None
                ).indices(dset.shape[0])
                some_dset_sn = dset[start::, shotnumkey]
                sni = np.isin(shotnum, some_dset_sn)

                # define index
                # NOTE: if index is empty (i.e. index.shape[0] == 0)
                #       then adding an int still returns an empty array
                index = np.where(np.isin(some_dset_sn, shotnum))[0]
                index += start

    # return calculated arrays
    return index.view(), sni.view()


def build_sndr_for_complex_dset(
    shotnum: np.ndarray,
    dset: h5py.Dataset,
    shotnumkey: str,
    cmap: ControlMap,
    cconfn: Any,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compares the **shotnum** numpy array to the specified "complex"
    dataset, **dset**, to determine which indices contain the desired
    shot number(s).  As a results, two numpy arrays are returned
    which satisfy the rule::

        shotnum[sni] = dset[index, shotnumkey]

    where **shotnum** is the original shot number array, **sni** is a
    boolean numpy array masking which shot numbers were determined to
    be in the dataset, and **index** is an array of indices
    corresponding to the desired shot number(s).

    A "complex" dataset is a dataset in which the data for MULTIPLE
    configurations is recorded.

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
    :param dset: dataset containing shot numbers
    :type dset: :class:`h5py.Dataset`
    :param str shotnumkey: field name in the dataset that contains
        the shot numbers
    :param cmap: mapping object for control device
    :param cconfn: configuration name for the control device
    :return: :code:`index` and :code:`sni` numpy arrays
    """
    # this is for a dataset that records data for multiple
    # configurations
    #
    # Initialize some vals
    n_configs = len(cmap.configs)

    # determine configkey
    # - configkey is the dataset field name for the column that contains
    #   the associated configuration name
    #
    configkey = ""
    for df in dset.dtype.names:
        if "configuration" in df.casefold():
            configkey = df
            break
    if configkey == "":
        raise ValueError(
            f"Can NOT find a configuration field in the control "
            f"({cmap.device_name}) dataset"
        )

    # find index
    if dset.shape[0] == n_configs:
        # only one possible shotnum, index can be 0 to n_configs-1
        #
        # NOTE: The HDF5 configuration field stores a string with the
        #       name of the configuration.  When reading that into a
        #       numpy array the string becomes a byte string (i.e. b'').
        #       When comparing with np.where() the comparing string
        #       needs to be encoded (i.e. cconfn.encode()).
        #
        only_sn = dset[0, shotnumkey]
        sni = np.where(shotnum == only_sn, True, False)

        # construct index
        if True not in sni:
            # shotnum does not contain only_sn
            index = np.empty(shape=0, dtype=np.uint32)
        else:
            config_name_arr = dset[0:n_configs, configkey]
            index = np.where(config_name_arr == cconfn.encode())[0]

            if index.size != 1:  # pragma: no cover
                # something went wrong...no configurations are found
                # and, thus, the routines assumption's do not match
                # the format of the dataset
                raise ValueError(
                    "The specified dataset is NOT consistent with the"
                    "routines assumptions of a complex dataset"
                )
    else:
        # get 1st and last shot number
        first_sn = dset[0, shotnumkey]
        last_sn = dset[-1, shotnumkey]

        # find sub-group index corresponding to the requested device
        # configuration
        config_name_arr = dset[0:n_configs, configkey]
        config_where = np.where(config_name_arr == cconfn.encode())[0]
        if config_where.size == 1:
            config_subindex = config_where[0]
        else:  # pragma: no cover
            # something went wrong...either no configurations
            # are found or the routine's assumptions do not
            # match the format of the dataset
            raise ValueError(
                "The specified dataset is NOT consistent with the"
                "routines assumptions of a complex dataset"
            )

        # construct index for remaining scenarios
        if n_configs * (last_sn - first_sn + 1) == dset.shape[0]:
            # shot numbers are sequential and there are n_configs per
            # shot number
            index = shotnum - first_sn

            # adjust index to correspond to associated configuration
            # - stretch by n_configs then shift by config_subindex
            #
            index = (n_configs * index) + config_subindex

            # build sni and filter index
            sni = np.where(index < dset.shape[0], True, False)
            index = index[sni]
        else:
            # shot numbers are NOT sequential
            step_front_read = shotnum[-1] - first_sn
            step_end_read = last_sn - shotnum[0]

            # construct index and sni
            if dset.shape[0] <= n_configs * (min(step_front_read, step_end_read) + 1):
                # dset.shape is smaller than the theoretical
                # sequential array
                dset_sn = dset[config_subindex::n_configs, shotnumkey]
                sni = np.isin(shotnum, dset_sn)
                index = np.where(np.isin(dset_sn, shotnum))[0]

                # adjust index to correspond to associated configuration
                index = (index * n_configs) + config_subindex
            elif step_front_read <= step_end_read:
                # extracting from the beginning of the array is the
                # smallest
                start = config_subindex
                stop = n_configs * (step_front_read + 1)
                stop += config_subindex
                step = n_configs
                some_dset_sn = dset[start:stop:step, shotnumkey]
                sni = np.isin(shotnum, some_dset_sn)
                index = np.where(np.isin(some_dset_sn, shotnum))[0]

                # adjust index to correspond to associated configuration
                index = (index * n_configs) + config_subindex
            else:
                # extracting from the end of the array is the
                # smallest
                start, stop, step = slice(
                    -n_configs * (step_end_read + 1), None, n_configs
                ).indices(dset.shape[0])
                start += config_subindex
                some_dset_sn = dset[start:stop:step, shotnumkey]
                sni = np.isin(shotnum, some_dset_sn)
                index = np.where(np.isin(some_dset_sn, shotnum))[0]

                # adjust index to correspond to associated configuration
                index = (index * n_configs) + start

    # return calculated arrays
    return index.view(), sni.view()


def condition_controls(hdf_file: File, controls: Any) -> List[Tuple[str, Any]]:
    """
    Conditions the **controls** argument for
    :class:`~.hdfreadcontrols.HDFReadControls` and
    :class:`~.hdfreaddata.HDFReadData`.

    :param hdf_file: HDF5 object instance
    :param controls: `controls` argument to be conditioned
    :return: list containing tuple pairs of control device name and
        desired configuration name

    :Example:

        >>> from bapsflib import lapd
        >>> f = lapd.File('sample.hdf5')
        >>> controls = ['Wavefrom', ('6K Compumotor', 3)]
        >>> conditioned_controls = condition_controls(f, controls)
        >>> conditioned_controls
        [('Waveform', 'config01'), ('6K Compumotor', 3)]

    .. admonition:: Condition Criteria

        #. Input **controls** should be
           :code:`Union[str, Iterable[Union[str, Tuple[str, Any]]]]`
        #. There can only be one control for each
           :class:`~bapsflib._hdf.maps.controls.types.ConType`.
        #. If a control has multiple configurations, then one must be
           specified.
        #. If a control has ONLY ONE configuration, then that will be
           assumed (and checked against the specified configuration).
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
        raise ValueError("controls argument is NULL")

    # make string a list
    if isinstance(controls, str):
        controls = [controls]

    # condition Iterable
    if isinstance(controls, Iterable):
        # all list items have to be strings or tuples
        if not all(isinstance(con, (str, tuple)) for con in controls):
            raise TypeError("all elements of `controls` must be of type string or tuple")

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
                        "('control name', config_name)"
                    )

                name = control[0]
                config_name = None if len(control) == 1 else control[1]

            # ensure proper control and configuration name are defined
            if name in [cc[0] for cc in new_controls]:
                raise ValueError(
                    f"Control device ({control}) can only have one occurrence in controls"
                )
            elif name in _fmap.controls:
                if config_name in _fmap.controls[name].configs:
                    # all is good
                    pass
                elif len(_fmap.controls[name].configs) == 1 and config_name is None:
                    config_name = list(_fmap.controls[name].configs)[0]
                else:
                    raise ValueError(
                        f"'{config_name}' is not a valid configuration name for "
                        f"control device '{name}'"
                    )
            else:
                raise ValueError(f"Control device ({name}) not in HDF5 file")

            # add control to new_controls
            new_controls.append((name, config_name))
    else:
        raise TypeError("`controls` argument is not Iterable")

    # re-assign `controls`
    controls = new_controls

    # enforce one control per contype
    checked = []
    for control in controls:
        # control is a tuple, not a string
        contype = _fmap.controls[control[0]].contype

        if contype in checked:
            raise TypeError("`controls` has multiple devices per contype")
        else:
            checked.append(contype)

    # return conditioned list
    return controls


def condition_shotnum(
    shotnum: Any, dset_dict: Dict[str, h5py.Dataset], shotnumkey_dict: Dict[str, str]
) -> np.ndarray:
    """
    Conditions the **shotnum** argument for
    :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls` and
    :class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`.

    :param shotnum: desired HDF5 shot numbers
    :param dset_dict: dictionary of all control dataset instances
    :param shotnumkey_dict: dictionary of the shot number field name
        for each control dataset in dset_dict
    :return: conditioned **shotnum** numpy array

    .. admonition:: Condition Criteria

        #. Input **shotnum** should be
           :code:`Union[int, List[int,...], slice, np.ndarray]`
        #. Any :math:`\mathbf{shotnum} \le 0` will be removed.
        #. A :code:`ValueError` will be thrown if the conditioned array
           is NULL.
    """
    # Acceptable `shotnum` types
    # 1. int
    # 2. slice() object
    # 3. List[int, ...]
    # 4. np.array (dtype = np.integer and ndim = 1)
    #
    # Catch each `shotnum` type and convert to numpy array
    #
    if isinstance(shotnum, int):
        if shotnum <= 0 or isinstance(shotnum, bool):
            raise ValueError(
                f"Valid `shotnum` ({shotnum}) not passed. Resulting array would be NULL."
            )

        # convert
        shotnum = np.array([shotnum], dtype=np.uint32)

    elif isinstance(shotnum, list):
        # ensure all elements are int
        if not all(isinstance(sn, int) for sn in shotnum):
            raise ValueError("Valid `shotnum` not passed. All values NOT int.")

        # remove shot numbers <= 0
        shotnum.sort()
        shotnum = list(set(shotnum))
        shotnum.sort()
        if min(shotnum) <= 0:
            # remove values less-than or equal to 0
            new_sn = [sn for sn in shotnum if sn > 0]
            shotnum = new_sn

        # ensure not NULL
        if len(shotnum) == 0:
            raise ValueError("Valid `shotnum` not passed. Resulting array would be NULL")

        # convert
        shotnum = np.array(shotnum, dtype=np.uint32)

    elif isinstance(shotnum, slice):
        # determine largest possible shot number
        last_sn = [
            dset_dict[cname][-1, shotnumkey_dict[cname]] + 1 for cname in dset_dict
        ]
        if shotnum.stop is not None:
            last_sn.append(shotnum.stop)
        stop_sn = max(last_sn)

        # get the start, stop, and step for the shot number array
        start, stop, step = shotnum.indices(stop_sn)

        # re-define `shotnum`
        shotnum = np.arange(start, stop, step, dtype=np.int32)

        # remove shot numbers <= 0
        shotnum = np.delete(shotnum, np.where(shotnum <= 0)[0])
        shotnum = shotnum.astype(np.uint32)

        # ensure not NULL
        if shotnum.size == 0:
            raise ValueError("Valid `shotnum` not passed. Resulting array would be NULL")

    elif isinstance(shotnum, np.ndarray):
        if shotnum.ndim != 1:
            shotnum = shotnum.squeeze()
        if (
            shotnum.ndim != 1
            or not np.issubdtype(shotnum.dtype, np.integer)
            or bool(shotnum.dtype.names)
        ):
            raise ValueError("Valid `shotnum` not passed")

        # remove shot numbers <= 0
        shotnum.sort()
        shotnum = np.delete(shotnum, np.where(shotnum <= 0)[0])
        shotnum = shotnum.astype(np.uint32)

        # ensure not NULL
        if shotnum.size == 0:
            raise ValueError("Valid `shotnum` not passed. Resulting array would be NULL")
    else:
        raise ValueError("Valid `shotnum` not passed")

    # return
    return shotnum


def do_shotnum_intersection(
    shotnum: np.ndarray, sni_dict: IndexDict, index_dict: IndexDict
) -> Tuple[np.ndarray, IndexDict, IndexDict]:
    """
    Calculates intersection of **shotnum** and all existing dataset
    shot numbers, **shotnum[sni]**.

    :param shotnum: desired HDF5 shot numbers
    :param sni_dict: dictionary of all dataset **sni** arrays
    :param index_dict:  dictionary of all dataset **index** arrays
    :return: intersected and re-calculated versions of :code:`index`
        and :code:`sni` numpy arrays

    .. admonition:: Recall Array Relationship

        .. code-block:: python

            shotnum[sni] = dset[index, shotnumkey]
    """
    # intersect shot numbers
    shotnum_intersect = shotnum
    for sni in sni_dict.values():
        shotnum_intersect = np.intersect1d(
            shotnum_intersect, shotnum[sni], assume_unique=True
        )
    if shotnum_intersect.shape[0] == 0:
        raise ValueError("Input `shotnum` would result in a NULL array")

    # now filter
    for cname in index_dict:
        sni = sni_dict[cname]
        mask_for_index = np.isin(shotnum[sni], shotnum_intersect)
        index_dict[cname] = index_dict[cname][mask_for_index]
        sni_dict[cname] = np.ones(shotnum_intersect.shape, dtype=bool)

    # update shotnum
    shotnum = shotnum_intersect

    # return
    return shotnum, sni_dict, index_dict
