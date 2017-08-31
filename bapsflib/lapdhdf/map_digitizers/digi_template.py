# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License:
#
# TODO: determine a default structure for all digitizer classes
#
import h5py


class hdfMap_digi_template(object):
    """
    Need to define class attribute __predefined_adc
    """
    def __init__(self, digi_group):
        # condition digi_group arg
        if isinstance(digi_group, h5py.Group):
            self.__digi_group = digi_group
        else:
            raise TypeError('arg digi_group is not of type h5py.Group')

        self.info = {'group name': digi_group.name.split('/')[-1],
                     'group path': digi_group.name}

    @property
    def digi_group(self):
        return self.__digi_group
