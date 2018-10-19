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
defined in module :mod:`bapslib._hdf.utils`.
"""
from typing import (Any, Iterable, List, Tuple)

from .file import File


def condition_controls(hdf_file: File,
                       controls: Any) -> List[Tuple[str, Any]]:
    """
    Conditions the **controls** argument for
    :class:`~.hdfreadcontrol.HDFReadControl` and
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
           :class:`~bapsflib._hdf.maps.controls.contype.ConType`.
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

            # ensure proper control and configuration name are defined
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

    # re-assign `controls`
    controls = new_controls

    # enforce one control per contype
    checked = []
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
