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
Package of package utility / helper functionality.
"""

__all__ = ["TableDisplay"]

from typing import List

from bapsflib.utils import decorators, exceptions, warnings


def _bytes_to_str(string: bytes | str) -> str:
    """Helper to convert a bytes literal to a utf-8 string."""
    if isinstance(string, str):
        return string

    if isinstance(string, bytes):
        try:
            return str(string, "utf-8")
        except UnicodeDecodeError:
            return str(string, "cp1252")

    raise TypeError(f"Argument 'string' is not of type str or bytes, got {type(string)}.")


class TableDisplay:
    def __init__(self, rows: List[List[str]], headers: List[str] | None = None):
        self._rows = rows
        self._rows_w_dividers = None
        self._headers = headers

        if not isinstance(rows, list):
            raise TypeError("rows must be a list")

        for row in rows:
            if not isinstance(row, list):
                raise TypeError("row must be a list")

            if not all(isinstance(entry, str) for entry in row):
                raise ValueError()

        if isinstance(headers, list):
            if len(headers) != self.ncols:
                raise ValueError("headers must be a list")

            if not all(isinstance(entry, str) for entry in headers):
                raise ValueError()
        elif headers is not None:
            raise TypeError("headers must be a list or None")

        self._cell_widths = self._calc_max_cell_widths()

    @property
    def cell_widths(self) -> List[int]:
        return self._cell_widths

    @property
    def headers(self) -> List[str]:
        return self._headers

    @property
    def rows(self) -> List[List[str]]:
        return self._rows

    @property
    def nrows(self) -> int:
        return len(self._rows)

    @property
    def ncols(self) -> int:
        return len(self._rows[0])

    def _calc_max_cell_widths(self):
        max_cel_widths = [len(entry) + 2 for entry in self.headers]
        for row in self.rows:
            for ii in range(len(max_cel_widths)):
                max_cel_widths[ii] = max(max_cel_widths[ii], len(row[ii]) + 2)

        return max_cel_widths

    def auto_insert_horizontal_dividers(self, on_columns: List[int] | None = None):
        if on_columns is None:
            return

        if not isinstance(on_columns, list):
            raise TypeError("on_column must be a int")

        if not all(isinstance(entry, int) for entry in on_columns):
            raise TypeError("All `on_column` entries must be a int.")

        on_columns = [val for val in set(on_columns) if 0 <= val < self.ncols]
        if len(on_columns) == 0:
            return

        _rows_w_dividers = self.rows.copy()

        for ii in range(self.nrows - 1, 0, -1):
            row = _rows_w_dividers[ii]

            for on_column in on_columns:
                if row[on_column] == "":
                    continue

                divider = []
                for jj in range(self.ncols):
                    _string = " " if jj < on_column else "-"
                    divider.append(_string * self.cell_widths[jj])

                _rows_w_dividers.insert(ii, divider)
                break

        self._rows_w_dividers = _rows_w_dividers

    def table_string(self) -> str:

        table_string = ""

        if self.headers is not None:
            for ii, entry in enumerate(self.headers):
                table_string += f"| {entry:<{self.cell_widths[ii]}} "
            table_string += "|\n"

            for ii, entry in enumerate(self.headers):
                table_string += f"+{'-' * (self.cell_widths[ii] + 2)}"
            table_string += "+\n"

        rows = self.rows if self._rows_w_dividers is None else self._rows_w_dividers
        for row in rows:
            for ii, entry in enumerate(row):
                table_string += f"| {entry:<{self.cell_widths[ii]}} "
            table_string += "|\n"

        return table_string
