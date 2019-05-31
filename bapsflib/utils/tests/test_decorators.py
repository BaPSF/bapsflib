# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2019 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
import inspect
import unittest as ut

from bapsflib._hdf import File as BaPSFFile
from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib.lapd import File as LaPDFile
from unittest import mock

from ..decorators import (with_bf, with_lapdf)


class TestWithBF(ut.TestCase):
    """
    Test case for decorator :func:`~bapsflib.utils.decorators.with_bf`.
    """

    f = NotImplemented  # type: FauxHDFBuilder

    @classmethod
    def setUpClass(cls) -> None:
        # create HDF5 file
        super().setUpClass()
        cls.f = FauxHDFBuilder()


    def setUp(self) -> None:
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()
        self.f.reset()

    @classmethod
    def tearDownClass(cls) -> None:
        # cleanup and close HDF5 file
        super().tearDownClass()
        cls.f.cleanup()

    @property
    def filename(self) -> str:
        return self.f.filename

    @staticmethod
    def foo_func():
        pass

    def foo_method(self):
        pass

    @mock.patch(BaPSFFile.__module__ + '.' + BaPSFFile.__qualname__,
                side_effect=BaPSFFile, autospec=True)
    def test_settings_by_decorator_kwargs(self, mock_bf_class):
        # define file settings to be based to decorator
        settings = {'filename': self.filename,
                    'control_path': 'Raw data + config',
                    'digitizer_path': 'Raw data + config',
                    'msi_path': 'MSI'}

        # create a function to mock
        def foo(bf: BaPSFFile, **kwargs):
            self.assertIsInstance(bf, BaPSFFile)
            bapsf_settings = {
                'filename': bf.filename,
                'control_path': bf.CONTROL_PATH,
                'digitizer_path': bf.DIGITIZER_PATH,
                'msi_path': bf.MSI_PATH,
            }
            return bapsf_settings
        mock_foo = mock.Mock(side_effect=foo, name='mock_foo', autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        # -- use decorator like a function --
        # wrapped_func = with_bf(func, **settings)
        func = with_bf(mock_foo, **settings)
        bf_settings = func()
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        for name in settings:
            self.assertEqual(settings[name], bf_settings[name])

        # reset mocks
        mock_foo.reset_mock()
        mock_bf_class.reset_mock()

        # -- mimic sugar syntax use of the decorator --
        #
        # @with_bf(**settings)
        #     def foo(bf):
        #         pass
        #
        func = with_bf(**settings)(mock_foo)
        bf_settings = func()
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        for name in settings:
            self.assertEqual(settings[name], bf_settings[name])

        # reset mocks
        mock_foo.reset_mock()
        mock_bf_class.reset_mock()

        # -- function keywords override decorator settings --
        bf_settings = func(control_path='a different path')
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        self.assertEqual('a different path', bf_settings['control_path'])
        for name in settings:
            if name == 'control_path':
                continue
            self.assertEqual(settings[name], bf_settings[name])

        # reset mocks
        mock_foo.reset_mock()
        mock_bf_class.reset_mock()

        # -- function arguments also override decorator settings --
        # create a function to mock
        def foo(filename: str, bf: BaPSFFile):
            self.assertIsInstance(bf, BaPSFFile)
            bapsf_settings = {
                'filename': bf.filename,
                'control_path': bf.CONTROL_PATH,
                'digitizer_path': bf.DIGITIZER_PATH,
                'msi_path': bf.MSI_PATH,
            }
            return bapsf_settings
        mock_foo = mock.Mock(side_effect=foo, name='mock_foo', autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        # wrap and test
        fname = settings.pop('filename')
        settings['filename'] = 'not a real file'
        func = with_bf(**settings)(mock_foo)
        bf_settings = func(fname)
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        self.assertEqual(bf_settings['filename'], fname)
        for name in settings:
            if name == 'filename':
                continue
            self.assertEqual(settings[name], bf_settings[name])

        # reset mocks
        mock_foo.reset_mock()
        mock_bf_class.reset_mock()

        # -- ValueError if filename never passed --
        # update settings s.t. no filename is specifiec
        if 'filename' in settings:
            del settings['filename']

        # create a function to mock
        def foo(bf: BaPSFFile):
            self.assertIsInstance(bf, BaPSFFile)
            bapsf_settings = {
                'filename': bf.filename,
                'control_path': bf.CONTROL_PATH,
                'digitizer_path': bf.DIGITIZER_PATH,
                'msi_path': bf.MSI_PATH,
            }
            return bapsf_settings
        mock_foo = mock.Mock(side_effect=foo, name='mock_foo', autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        # wrap and test
        func = with_bf(**settings)(foo)
        self.assertRaises(ValueError, func)

        # -- if path not specified then class default is assumed --
        # update settings s.t. no filename is specified
        settings['filename'] = self.filename
        if 'control_path' in settings:
            del settings['control_path']

        # create a function to mock
        def foo(bf: BaPSFFile):
            self.assertIsInstance(bf, BaPSFFile)
            bapsf_settings = {
                'filename': bf.filename,
                'control_path': bf.CONTROL_PATH,
                'digitizer_path': bf.DIGITIZER_PATH,
                'msi_path': bf.MSI_PATH,
            }
            return bapsf_settings

        mock_foo = mock.Mock(side_effect=foo, name='mock_foo', autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        # wrap and test
        func = with_bf(**settings)(foo)
        bf_settings = func()
        for name in bf_settings:
            if name == 'control_path':
                cp_default = inspect.signature(BaPSFFile).parameters[
                    'control_path'].default
                self.assertEqual(bf_settings[name], cp_default)
            else:
                self.assertEqual(bf_settings[name], settings[name])

    @mock.patch(BaPSFFile.__module__ + '.' + BaPSFFile.__qualname__,
                side_effect=BaPSFFile, autospec=True)
    def test_settings_by_function_args(self, mock_bf_class):
        # BaPSF file settings can also be pass by either function args or
        # kwargs
        #
        # define file settings to be based to decorator
        settings = {'filename': self.filename,
                    'control_path': 'Raw data + config',
                    'digitizer_path': 'Raw data + config',
                    'msi_path': 'MSI'}

        # create a function to mock
        def foo(filename: str, bf: BaPSFFile, **kwargs):
            self.assertIsInstance(bf, BaPSFFile)
            bapsf_settings = {
                'filename': bf.filename,
                'control_path': bf.CONTROL_PATH,
                'digitizer_path': bf.DIGITIZER_PATH,
                'msi_path': bf.MSI_PATH,
            }
            return bapsf_settings

        # define function mock
        mock_foo = mock.Mock(side_effect=foo, name='mock_foo', autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        # wrap and test
        # - this is equivalent to writing
        #
        #     @with_bf
        #     def foo(filename, bf, **kwargs):
        #         pass
        #
        fname = settings.pop('filename')
        func = with_bf(mock_foo)
        bf_settings = func(fname, **settings)
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        for name in bf_settings:
            if name == 'filename':
                self.assertEqual(bf_settings[name], fname)
            else:
                self.assertEqual(bf_settings[name], settings[name])

        # reset mocks
        mock_bf_class.reset_mock()
        mock_foo.reset_mock()

        # settings defines 'control_path'=None
        settings['control_path'] = None
        bf_settings = func(fname, **settings)
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        self.assertEqual(
            bf_settings['control_path'],
            inspect.signature(BaPSFFile).parameters['control_path'].default
        )

        # reset mocks
        mock_bf_class.reset_mock()
        mock_foo.reset_mock()

        # settings defines 'filename'=None
        self.assertRaises(ValueError, func, None)


if __name__ == '__main__':
    ut.main()
