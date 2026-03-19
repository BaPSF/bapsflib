__all__ = ["MapTestBase"]

from bapsflib._hdf.maps.tests.fauxhdfbuilder import FauxHDFBuilder
from bapsflib.utils.tests import BaPSFTestCase


class MapTestBase(BaPSFTestCase):
    """Base test class for all mapping test classes."""

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
