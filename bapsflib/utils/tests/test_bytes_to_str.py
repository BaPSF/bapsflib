import unittest as ut

from bapsflib.utils import _bytes_to_str


class TestBytesToStr(ut.TestCase):
    """Tests for `bapsflib.utils._bytes_to_str`."""

    def test_raises(self):
        for val in [5, None, True, (1, 2, 3)]:
            with self.subTest(val=val):
                self.assertRaises(TypeError, _bytes_to_str, val)

    def test_valid_vals(self):
        conditions = [
            ("Hello", "Hello"),
            (b"Goodbye", "Goodbye"),
            (b"doesn't", "doesn't"),
            (b"doesn\x92t", "doesn’t"),
        ]
        for inputs, expected in conditions:
            with self.subTest(inputs=inputs, expected=expected):
                self.assertEqual(_bytes_to_str(inputs), expected)


if __name__ == "__main__":
    ut.main()
