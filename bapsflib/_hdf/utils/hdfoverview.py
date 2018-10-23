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
import os
import pprint as pp
import sys

from bapsflib import __version__ as bapsf_vers
from datetime import datetime

from .file import File
from ..maps.controls.templates import HDFMapControlTemplate
from ..maps.digitizers.templates import HDFMapDigiTemplate
from ..maps.msi.templates import HDFMapMSITemplate


class HDFOverview(object):
    """
    Reports an overview of the HDF5 file mapping.
    """
    def __init__(self, hdf_obj: File):
        """
        :param hdf_obj: HDF5 file map object
        :type hdf_obj: :class:`~bapsflib._hdf.utils.file.File`
        """
        super().__init__()

        # store an instance of the HDF5 file object and map
        if isinstance(hdf_obj, File):
            self._file = hdf_obj
            self._fmap = hdf_obj.file_map
        else:
            raise ValueError('input arg is not of type HDFMap')

    def print(self):
        """
        Print full Overview Report.
        """
        # TODO: add reporting of 'data run sequence'
        # TODO: add reporting of motion device's 'motion list'
        #
        # ------ Print Header                                     ------
        print('=' * 72)
        print('{} Overview'.format(self._file.info['file']))
        print('Generated by bapsflib (v' + bapsf_vers + ')')
        print('Generated date: '
              + datetime.now().strftime('%-m/%-d/%Y %-I:%M:%S %p'))
        print('=' * 72 + '\n\n')

        # ------ Print General Info                               ------
        self.report_general()

        # ------ Print Discovery Report                           ------
        self.report_discovery()

        # ------ Print Detailed Reports                           ------
        self.report_details()

    def save(self, filename):
        """
        Saves the HDF5 overview to a text file.

        :param str filename: name of text file to save the overview
            report. Set :code:`True` to save to a text with the same
            name and path as the HDF5 file.
        """
        if filename is True:
            # use the same name as the HDF5 file
            filename = os.path.splitext(self._file.filename)[0]\
                       + '.txt'

        # write to file
        with open(filename, 'w') as of:
            sys.stdout = of
            self.print()

        # return to standard output
        sys.stdout = sys.__stdout__

    def report_general(self):
        """
        Prints general HDF5 file info.
        """
        # print basic file info
        print('Filename:     {}'.format(self._file.info['file']))
        print('Abs. Path:    {}'.format(
            self._file.info['absolute file path']))

    def report_discovery(self):
        """
        Prints a discovery (brief) report of all detected MSI
        diagnostics, digitizers, and control devices.
        """
        # print header
        print('\n\nDiscovery Report')
        print('----------------\n')

        # print digitizers
        self.control_discovery()
        print('\n')

        # print digitizers
        self.digitizer_discovery()
        print('\n')

        # print msi
        self.msi_discovery()
        print('\n')

        # print unknowns
        self.unknowns_discovery()

    def report_details(self):
        """
        Prints a detailed report of all detected MSI diagnostics,
        digitizers, and control devices.
        """
        # print header
        print('\n\nDetailed Reports')
        print('-----------------')

        # digitizer report
        self.report_digitizers()

        # control devices report
        self.report_controls()

        # msi report
        self.report_msi()

    def control_discovery(self):
        """
        Prints a discovery report of the Control devices.
        """
        # is there a control group
        _path = self._fmap.DEVICE_PATHS['control']
        _detected = _path in self._file

        # print number of diagnostics
        ndevices = len(self._fmap.controls)
        item = 'Control devices ({})'.format(ndevices)
        status_print(item, '', '', indent=0)

        # print status to screen
        item = _path + '/'
        found = 'found' if _detected else 'missing'
        status_print(item, found, '', indent=1)

        # list diagnostics
        for device in self._fmap.controls:
            status_print(device, '', '', indent=2)

    def digitizer_discovery(self):
        """
        Prints a discovery report of the Digitizer devices.
        """
        # is there a digitizer group
        _path = self._fmap.DEVICE_PATHS['digitizer']
        _detected = _path in self._file

        # print number of diagnostics
        ndevices = len(self._fmap.digitizers)
        item = 'Digitizer devices ({})'.format(ndevices)
        status_print(item, '', '', indent=0)

        # print status to screen
        item = _path + '/'
        found = 'found' if _detected else 'missing'
        status_print(item, found, '', indent=1)

        # list diagnostics
        for device in self._fmap.digitizers:
            if device == self._fmap.main_digitizer.device_name:
                device += " (main)"
            status_print(device, '', '', indent=2)

    def msi_discovery(self):
        """
        Prints a discovery report of the MSI devices.
        """
        # is there a MSI group
        _path = self._fmap.DEVICE_PATHS['msi']
        _detected = _path in self._file

        # print number of diagnostics
        ndevices = len(self._fmap.msi)
        item = 'MSI devices ({})'.format(ndevices)
        status_print(item, '', '', indent=0)

        # print status to screen
        item = _path + '/'
        found = 'found' if _detected else 'missing'
        status_print(item, found, '', indent=1)

        # list diagnostics
        for device in self._fmap.msi:
            status_print(device, '', '', indent=2)

    def unknowns_discovery(self):
        """
        Prints a discovery report of the Unknown devices.
        """
        ndevices = len(self._fmap.unknowns)
        item = 'Unknowns ({})'.format(ndevices)
        note = 'aka unmapped'
        status_print(item, note, '', indent=0)

        # list unknowns
        for device in self._fmap.unknowns:
            status_print(device, '', '', indent=1)

    def report_msi(self, name=None):
        """
        Prints to screen a report of detected MSI diagnostics and
        their configurations.

        :param str name: name of MSI diagnostic. If :code:`None` or
            `name` is not among MSI diagnostics, then all MSI
            diagnostics are printed.
        """
        # gather configs to print
        if name in self._fmap.msi:
            _dmap = {name, self._fmap.msi[name]}
        else:
            name = None
            _dmap = self._fmap.msi

        # print heading
        title = 'MSI Diagnostic Report'
        if name is not None:
            title += ' ({} ONLY)'.format(name)
        print('\n\n' + title)
        print('^' * len(title) + '\n')

        # print msi diagnostic config
        for name, _map in _dmap.items():
            # print msi diag name
            status_print(_map.device_name, '', '')

            # print path to diagnostic
            item = 'path:  ' + _map.info['group path']
            status_print(item, '', '', indent=1)

            # print the configs dict
            self.report_msi_configs(_map)

    @staticmethod
    def report_msi_configs(msi: HDFMapMSITemplate):
        """
        Print to screan information about the passed MSI configuration.

        :param msi: a MSI mapping object
        """
        # print configs title
        status_print('configs', '', '', indent=1)

        # pretty print the configs dict
        ppconfig = pp.pformat(msi.configs)
        for line in ppconfig.splitlines():
            status_print(line, '', '', indent=2)

    def report_digitizers(self, name=None):
        """
        Prints to screen a report of detected digitizers and their
        configurations.

        :param str name: name of digitizer. If :code:`None` or
            `name` is not among digitizers, then all digitizers are
            printed.
        """
        # gather configs to print
        if name in self._fmap.digitizers:
            _dmap = {name, self._fmap.digitizers[name]}
        else:
            name = None
            _dmap = self._fmap.digitizers

        # print heading
        title = 'Digitizer Report'
        if name is not None:
            title += ' ({} ONLY)'.format(name)
        print('\n\n' + title)
        print('^' * len(title) + '\n')

        # print digitizer config
        for name, _map in _dmap.items():
            # print digitizer name
            item = name
            if name == self._fmap.main_digitizer.device_name:
                item += ' (main)'
            status_print(item, '', '')

            # print adc's
            item = "adc's:  {}".format(_map.device_adcs)
            status_print(item, '', '', indent=1)

            # print digitizer configs
            self.report_digitizer_configs(_map)

    @staticmethod
    def report_digitizer_configs(digi: HDFMapDigiTemplate):
        """
        Prints to screen information about the passed digitizer
        configuration(s).

        :param digi: a digitizer mapping object
        """
        nconfigs = len(digi.configs)
        if nconfigs != 0:
            nconf_active = len(digi.active_configs)

            item = 'Configurations Detected ({})'.format(nconfigs)
            note = '({0} active, {1} inactive)'.format(
                nconf_active, nconfigs - nconf_active)
            status_print(item, '', note, indent=1)

            for cname, config in digi.configs.items():
                # print configuration name
                item = cname
                found = ''
                note = 'active' if config['active'] else 'NOT active'
                status_print(item, found, note, indent=2)

                # print active adc's
                item = "adc's (active):  {}".format(config['adc'])
                status_print(item, '', '', indent=3)

                # print path for config
                item = 'path: ' + config['config group path']
                status_print(item, '', '', indent=3)

                # print adc details for configuration
                for adc in config['adc']:
                    # adc name
                    item = adc + ' adc connections'
                    status_print(item, '', '', indent=3)

                    # print adc header
                    line_indent = ('|   ' * 4) + '+-- '
                    line = line_indent + '(brd, [ch, ...])'
                    line = line.ljust(51)
                    line += 'bit'.ljust(5)
                    line += 'clock rate'.ljust(13)
                    line += 'nshotnum'.ljust(10)
                    line += 'nt'.ljust(10)
                    line += 'shot ave.'.ljust(11)
                    line += 'sample ave.'
                    print(line)

                    # adc connections
                    nconns = len(config[adc])
                    for iconn in range(nconns):
                        conns = config[adc][iconn][0:2]
                        adc_stats = config[adc][iconn][2]

                        # construct and print line
                        line = line_indent + str(conns)
                        line = line.ljust(51)
                        line += str(adc_stats['bit']).ljust(5)
                        line += '{}'.format(
                            adc_stats['clock rate']).ljust(13)
                        line += str(adc_stats['nshotnum']).ljust(10)
                        line += str(adc_stats['nt']).ljust(10)
                        line += str(
                            adc_stats['shot average (software)']
                        ).ljust(11)
                        line += str(
                            adc_stats['sample average (hardware)'])
                        print(line)
        else:
            status_print('Configurations Detected (0)', '', '',
                         indent=1)

    def report_controls(self, name=None):
        """
        Prints to screen a detailed report of detected control devices
        and their configuration(s).

        :param str name: name of control device. If :code:`None` or
            `name` is not among controls, then all control devices are
            printed.
        """
        # gather configs to print
        if name in self._fmap.controls:
            _dmap = {name, self._fmap.controls[name]}
        else:
            name = None
            _dmap = self._fmap.controls

        # print heading
        title = 'Control Device Report'
        if name is not None:
            title += ' ({} ONLY)'.format(name)
        print('\n\n' + title)
        print('^' * len(title) + '\n')

        # print control config
        for name, _map in _dmap.items():
            # print control name
            status_print(_map.device_name, '', '')

            # print path to control
            item = 'path:     ' + _map.info['group path']
            status_print(item, '', '', indent=1)

            # print path to contype
            item = 'contype:  {}'.format(_map.contype)
            status_print(item, '', '', indent=1)

            # print configurations
            self.report_control_configs(_map)

    @staticmethod
    def report_control_configs(control: HDFMapControlTemplate):
        """
        Prints to screen information about the passed control device
        configuration(s).

        :param control: a control device mapping object
        """
        nconfigs = len(control.configs)
        if nconfigs != 0:
            # display number of configurations
            item = 'Configurations Detected ({})'.format(nconfigs)
            status_print(item, '', '', indent=1)

            # display config values
            for cname, config in control.configs.items():
                # print config_name
                status_print(cname, '', '', indent=2)

                # get pretty print string
                ppconfig = pp.pformat(config)
                for line in ppconfig.splitlines():
                    status_print(line, '', '', indent=3)

        else:
            item = 'Configurations Detected (0)'
            status_print(item, '', '', indent=1)


def status_print(first: str, second: str, third: str,
                 indent=0, onetwo_pad=' ', second_tab=55):
    """
    Stylistic status printing for :class:`HDFOverview`.

    :param first: string for 1st column
    :param second: string for 2nd column
    :param third: string for 3rd column
    :param int indent: num. of indentations for 1st column display
    :param str onetwo_pad: one character string for pad style
        between 1st and 2nd column
    :param int second_tab: number of characters between start of string
        and start of 2nd column

    :Example:
        .. code-block:: python

            >>> status_print('one', 'two', 'three', second_tab=15)
            one            two    three
            >>> status_print('one', 'two', 'three', second_tab=15,
            ...              indent=2, onetwo_pad='~')
            |   +-- one    two    three



    """
    note_tab = 7

    if indent == 0:
        str_print = ''
    elif indent == 1:
        str_print = '+-- '
    else:
        str_print = ('|   ' * (indent - 1)) + '+-- '
    str_print += str(first) + ' '
    str_print = str_print.ljust(second_tab - 1, onetwo_pad) + ' '
    str_print += str(second).ljust(note_tab) + str(third)

    print(str_print)
