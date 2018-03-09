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
# TODO: create a save to file for report
#
# Check Template
#
# Generated by LaPD ~~~~~~~~~~~~~~~~ yes    (v1.1)
# Item                               Found  Note
# MSI/ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ yes
# |-- Discharge ~~~~~~~~~~~~~~~~~~~~ yes    in mapping context
# |-- Gas pressure ~~~~~~~~~~~~~~~~~ yes    in mapping context
# |-- Heater ~~~~~~~~~~~~~~~~~~~~~~~ yes    in mapping context
# |-- Interferometer array ~~~~~~~~~ yes    in mapping context
# |-- Magnetic field ~~~~~~~~~~~~~~~ yes    in mapping context
# Raw data + config/ ~~~~~~~~~~~~~~~ yes
# |-- Data run sequence ~~~~~~~~~~~~ yes
# |-- Control Devices ~~~~~~~~~~~~~~ yes
# |   |-- (list group names)
# |-- Digitizers ~~~~~~~~~~~~~~~~~~~ yes
# |   |-- (list group names)
# |-- Unknown ~~~~~~~~~~~~~~~~~~~~~~ yes
# |   |-- (list group names)
#
# Digitizer Report
# |-- SIS 3301 (main)
# |-- |-- Configurations Detected (#)       (# active, # inactive)
# |-- |-- |-- 'config name'                 used/ not used
# |-- |-- |-- |-- Path: 'path to config group'
# |-- |-- |-- |-- 'SIS 3301' adc connections    (brd, [ch, ...])
# |-- |-- |-- |-- |-- (0, [1,2,5])          ##-bit, ## MHz,
#                                           shot ave. #, sample ave. #
#
# Control Report
# |-- 6K Compumotor
# |-- |-- contype: 'motion'
# |-- |-- Configurations Detected (#)
# |-- |-- |-- 'config name'
# |-- Waveform
import h5py
import os
import sys

from .hdferrors import NotHDFFileError, NotLaPDHDFError, NoMSIError
from .hdfmapper import hdfMap

from contextlib import contextmanager


class hdfCheck(object):
    """
    Initiates the HDF5 mapping constructor
    (:class:`~.hdfmapper.hdfMap`) and prints a file report to screen
    (or file).
    """
    def __init__(self, hdf_obj, silent=False, save_report=False):
        """
        :param hdf_obj: HDF5 file object
        :type hdf_obj: :class:`h5py.File`
        :param bool silent: :code:`False` (default). Set :code:`True` to
            suppress command line printout of file report.
        :param save_report: :code:`False` (default). Set :code:`True` to
            save file report to a txt file of the same name as the HDF5
            file or set to string to specify file name.
        :type save_report: bool or str
        """
        # TODO: enable :data:`silent` keyword
        # TODO: enable :data:`save_report` keyword

        # store an instance of the HDF5 file object for hdfCheck
        self.__hdf_obj = hdf_obj

        # determine if file was written by the LaPD
        try:
            self._hdf_lapd_version = ''
            status = self.is_lapd_generated(silent=False)[0]
        except AttributeError:
            raise NotHDFFileError

        # build mappings
        if status:
            self.__hdf_map = hdfMap(hdf_obj)
            self.full_check()

    def full_check(self):
        """
        Run all pre-defined file checks.
        """
        # TODO: add a self.report_msi
        # TODO: add a self.report_data_run_sequence
        # TODO: add a self.report_motion_lists
        #
        status_print('Item', 'Found', 'Note', item_found_pad=' ')

        # HDF5 brief report
        status = self.exist_msi(silent=False)
        if status:
            self.check_all_msi_diagnostics(silent=False)
        status = self.exist_data_group(silent=False)
        if status:
            self.exist_data_run_sequence(silent=False)
            self.exist_digitizers(silent=False)
            self.exist_controls(silent=False)

        # Digitizer Detail Report
        if self.__hdf_map.has_digitizers:
                self.report_digitizers(silent=False)

    def is_lapd_generated(self, silent=True):
        """
        Checks the loaded HDF5 file to see if it was generated by the
        LaPD Control System.

        :param silent:
        :return:
        """
        is_lapd = False
        for key in self.__hdf_obj.attrs:
            if 'lapd' in key.casefold() and 'version' in key.casefold():
                self._hdf_lapd_version = \
                    self.__hdf_obj.attrs[key].decode('utf-8')
                is_lapd = True
                break

        item = 'Generated by LaPD'
        found = 'yes' if is_lapd else 'no'
        note = '(v{})\n'.format(self._hdf_lapd_version) if is_lapd \
            else '\n'
        with control_print_out(silent):
            status_print(item, found, note)

        if not is_lapd:
            raise NotLaPDHDFError

        return is_lapd, self._hdf_lapd_version

    def exist_msi(self, silent=True):
        """
        Check for the existence of the MSI Group.

        :param silent:
        :return:
        """
        # go to a Null print if silent=True
        if silent:
            sys.stdout = open(os.devnull, 'w')

        # the __hdf_map.msi attribute is None if hdfMap() can not find
        # the msi groupd defined by __hdf_map.msi_group
        # if self.__hdf_map.msi is None:
        #     msi_detected = False
        # else:
        #     msi_detected = True
        msi_detected = self.__hdf_map.has_msi_group

        # print status to screen
        item = self.__hdf_map._MSI_GNAME + '/'
        found = 'yes' if msi_detected else 'no'
        status_print(item, found, '')

        # raise Error if MSI is not detected
        if not msi_detected:
            raise NoMSIError

        # return to normal print
        if silent:
            sys.stdout = sys.__stdout__

        return msi_detected

    def exist_msi_diagnostic(self, diag_group_name, silent=True):
        """
        Check for an MSI diagnostic group by the name of
        diag_group_name.

        :param diag_group_name
        :param silent:
        :return:
        """
        if silent:
            sys.stdout = open(os.devnull, 'w')

        diag_detected = False

        # scan if diag_group_name is among the sub-groups in the MSI
        # group
        if diag_group_name in self.__hdf_map.msi.found_diagnostics:
            diag_detected = True

        # check if the diag_group_name is known in the pre-defined
        # mapping context
        diag_in_context = \
            self.__hdf_map.msi.is_diagnostic_in_context(diag_group_name)

        item = diag_group_name + ' '
        found = 'yes' if diag_detected else 'no'
        note = 'in mapping context' if diag_in_context else ''
        status_print(item, found, note, indent=1)

        if silent:
            sys.stdout = sys.__stdout__

        return diag_detected

    def check_all_msi_diagnostics(self, silent=True):
        """
        Check for all pre-defined MSI Diagnostic groups.

        Pre-defined diagnostic group are set in
        self._msi_diagnostic_groups,

        :param silent:
        :return:
        """
        try:
            for ii, diag in \
                    enumerate(self.__hdf_map.msi.found_diagnostics):
                self.exist_msi_diagnostic(diag, silent=silent)
        except TypeError:
            pass

    def exist_data_group(self, silent=True):
        """
        Check for the existence of the 'Raw data + config' Group.

        :param silent:
        :return:
        """
        # go to a Null print if silent=True
        if silent:
            sys.stdout = open(os.devnull, 'w')

        # the __hdf_map.digitizer attribute is None if hdfMap() can not
        # find the data group defined by __hdf_map.data_group
        data_detected = self.__hdf_map.has_data_group

        # print status to screen
        item = self.__hdf_map._DATA_GNAME + '/ '
        found = 'yes' if data_detected else 'no'
        status_print(item, found, '')

        # return to normal print
        if silent:
            sys.stdout = sys.__stdout__

        return data_detected

    def exist_data_run_sequence(self, silent=True):
        """
        Print the 'Data run sequence' check results from the generated
        HDF5 mapping.

        :param silent:
        """
        # go to a Null print if silent=True
        if silent:
            sys.stdout = open(os.devnull, 'w')

        # Check if 'Data run sequence' was discovered
        item = 'Data run sequence'
        found = ''
        note = '' if self.__hdf_map.has_data_run_sequence \
            else 'None known'
        status_print(item, found, note, indent=1, item_found_pad=' ')

        # return to normal print
        if silent:
            sys.stdout = sys.__stdout__

    def exist_digitizers(self, silent=True):
        """
        Print the digitizer check results from the generated HDF5
        mapping.

        :param silent:
        """
        # go to a Null print if silent=True
        if silent:
            sys.stdout = open(os.devnull, 'w')

        # Check if any digitizers were discovered
        item = 'Digitizers'
        found = ''
        if self.__hdf_map.has_digitizers:
            item += ' ({})'.format(len(self.__hdf_map.digitizers))
            note = ''
        else:
            item += ' (0)'
            note = 'None known'
        status_print(item, found, note, indent=1, item_found_pad=' ')

        # Print list of digitizers
        if self.__hdf_map.has_digitizers:
            for key in self.__hdf_map.digitizers:
                item = key
                if key in self.__hdf_map.main_digitizer.info[
                        'group name']:
                    item += ' (main)'
                status_print(item, '', '', indent=2, item_found_pad=' ')

        # return to normal print
        if silent:
            sys.stdout = sys.__stdout__

    def exist_controls(self, silent=True):
        """
        Print the control device check results from the generated HDF5
        mapping.

        :param silent:
        """
        # go to a Null print if silent=True
        if silent:
            sys.stdout = open(os.devnull, 'w')

        # Check if any motion lists were discovered
        item = 'Control Devices'
        found = ''
        if self.__hdf_map.has_controls:
            item += ' ({})'.format(len(self.__hdf_map.controls))
            note = ''
        else:
            item += ' (0)'
            note = 'None known'
        status_print(item, found, note, indent=1, item_found_pad=' ')

        # Print list of control devices
        if self.__hdf_map.has_controls:
            for control in self.__hdf_map.controls:
                item = control
                found = ''
                note = ''
                status_print(item, found, note,
                             indent=2, item_found_pad=' ')

        # return to normal print
        if silent:
            sys.stdout = sys.__stdout__

    def report_digitizers(self, silent=True):
        """
        Prints to screen a report of all detected digitizers and their
        configurations.

        :param silent: True will null print report, False will be
            standard print output
        """
        # go to a Null print if silent=True
        if silent:
            sys.stdout = open(os.devnull, 'w')

        # print heading
        status_print('\nDigitizer Report', '', '', item_found_pad=' ')

        # print digitizer config
        for key in self.__hdf_map.digitizers:
            # print digitizer name
            item = key
            if key in self.__hdf_map.main_digitizer.info['group name']:
                item += ' (main)'
            status_print(item, '', '', indent=1, item_found_pad=' ')

            # print digitizer configs
            self.report_digitizer_configs(
                self.__hdf_map.digitizers[key], silent=silent)

        # return to normal print
        if silent:
            sys.stdout = sys.__stdout__

    @staticmethod
    def report_digitizer_configs(digi, silent=True):
        """
        Prints to screen information about the passed digitizer
        configurations.

        :param digi: an instance of a single member of
            `hdfMap.digitizers`
        :param silent: True will null print report, False will be
            standard print output
        """
        # go to a Null print if silent=True
        if silent:
            sys.stdout = open(os.devnull, 'w')

        if len(digi.configs) != 0:
            nconfigs = len(digi.configs)
            nconf_active = 0
            for key in digi.configs:
                if digi.configs[key]['active']:
                    nconf_active += 1

            item = 'Configurations Detected ({})'.format(nconfigs)
            note = '({0} active, {1} inactive)'.format(
                nconf_active, nconfigs - nconf_active)
            status_print(item, '', note, indent=2, item_found_pad=' ')

            for conf in digi.configs:
                # print configuration name
                item = conf
                found = ''
                note = 'used' if digi.configs[conf]['active'] \
                    else 'not used'
                status_print(item, found, note, indent=3,
                             item_found_pad=' ')

                # print path for config
                item = 'Path: '\
                       + digi.configs[conf]['group path']
                status_print(item, '', '', indent=4, item_found_pad=' ')

                # print adc details for configuration
                for adc in digi.configs[conf]['adc']:
                    # adc name
                    item = adc + ' adc connections'
                    note = '(brd, [ch, ...])'
                    status_print(item, '', note, indent=4,
                                 item_found_pad=' ')

                    # adc connections
                    nconns = len(digi.configs[conf][adc])
                    for iconn in range(nconns):
                        conns = digi.configs[conf][adc][iconn][0:2]
                        adc_stats = digi.configs[conf][adc][
                            iconn][2]
                        item = '{}'.format(conns)
                        note = '{0}-bit, {1} {2}'.format(
                            adc_stats['bit'],
                            adc_stats['sample rate'][0],
                            adc_stats['sample rate'][1])
                        note += ', shot ave. {0}'.format(
                            adc_stats['shot average (software)'])
                        note += ', sample ave. {0}'.format(
                            adc_stats['sample average (hardware)'])
                        status_print(item, '', note, indent=5,
                                     item_found_pad=' ')
        else:
            status_print('Configurations Detected', '', 'None',
                         indent=2, item_found_pad=' ')

        # return to normal print
        if silent:
            sys.stdout = sys.__stdout__

    def get_hdf_mapping(self):
        """
        :return: an instance of the file mapping
            :py:class:`lapdhdf.hdfmapper.hdfMap`
        """
        return self.__hdf_map


@contextmanager
def control_print_out(silent):
    # go to a Null print if silent=True
    if silent:
        sys.stdout = open(os.devnull, 'w')

    yield sys.stdout

    # return to normal print
    if silent:
        sys.stdout = sys.__stdout__


def status_print(item, found, note, indent=0, item_found_pad='~'):
    """
    Stylistic status printing for :py:class:`hdfCheck`

    :param item: `str` for item (1st) column
    :param found: `str` for found (2nd) column
    :param note: `str` for note (3rd) column
    :param indent: `int` num. of indentations for `item` display
    :param item_found_pad: `str` pad style between `item` and `found`
    """
    _found_tab = 55
    _note_tab = 7

    str_print = ('|-- ' * indent) + str(item) + ' '
    str_print = str_print.ljust(_found_tab - 1, item_found_pad) + ' '
    str_print += str(found).ljust(_note_tab) + str(note)

    print(str_print)