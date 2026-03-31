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
__all__ = ["TestBase", "with_bf"]

from bapsflib._hdf.maps.tests import FauxHDFBuilder
from bapsflib.utils.decorators import with_bf
from bapsflib.utils.tests import BaPSFTestCase


class TestBase(BaPSFTestCase):
    """Base test class for all test classes here."""

    def setUp(self) -> None:
        if not hasattr(self, "_f") or self._f is None:
            self._f = FauxHDFBuilder()

    def tearDown(self) -> None:
        self.f.cleanup()
        self._f = None

    @property
    def f(self) -> FauxHDFBuilder:
        return self._f

    @property
    def filename(self) -> str:
        return self.f.filename

    @property
    def control_path(self) -> str:
        return "Raw data + config"

    @property
    def digitizer_path(self) -> str:
        return "Raw data + config"

    @property
    def msi_path(self) -> str:
        return "MSI"
