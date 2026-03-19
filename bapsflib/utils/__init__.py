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
    """
    Class designed to generated the brief summary tables used in the
    ``__str__`` and ``__repr__`` methods of
    `~bapsflib._hdf.maps.digitizers.map_digis.HDFMapDigitizers` and
    `~bapsflib._hdf.maps.controls.map_controls.HDFMapControls`.
    """

    def __init__(self, rows: List[List[str]], headers: List[str] | None = None):
        """
        Parameters
        ----------
        rows : List[List[str]]
            List of table rows where each row is a list of strings being
            the contents of the associated row-column cell.  For
            example, ``rows[4][3]`` would be the cell contents of row 5
            and column 4.

        headers : List[str]
            List of strings specifying the table column headers.  `None`
            if table has no headers. (DEFAULT: `None`)
        """
        self._rows = rows
        self._rows_w_dividers = None
        self._headers = headers

        if not isinstance(rows, list):
            raise TypeError(
                f"Argument `rows` must be a list of lists, got type {type(rows)}."
            )

        for row in rows:
            if not isinstance(row, list):
                raise TypeError(
                    f"Argument `rows` must be a list of lists, got type {type(rows)}."
                )

            if not all(isinstance(entry, str) for entry in row):
                raise ValueError("All entries in argument `rows` bust be a string.")

        if isinstance(headers, list):
            if len(headers) != self.ncols:
                raise ValueError(
                    "Argument `headers` does NOT contain the same number of "
                    f"columns ({len(headers)}) as the `rows` argument ({self.ncols}).)"
                )

            if not all(isinstance(entry, str) for entry in headers):
                raise ValueError("All entries in argument `headers` bust be a string.")
        elif headers is not None:
            raise TypeError(
                f"Argument `headers` must be a list of string or None, "
                f"got type {type(headers)}."
            )

        self._cell_widths = self._calc_max_cell_widths()

    @property
    def cell_widths(self) -> List[int]:
        """
        List of cell widths of the table.  Length equal to the number
        of columns, `ncols`.
        """
        return self._cell_widths

    @property
    def headers(self) -> List[str] | None:
        """
        List of table headers.  Length equal to the number of columns,
        `ncols`.

        `None` if table has no headers.
        """
        return self._headers

    @property
    def rows(self) -> List[List[str]]:
        """
        List of table rows where each row is a list of strings being
        the contents of the associated row-column cell.

        For example, ``rows[4][3]`` would be the cell contents of row 5
        and column 4.
        """
        return self._rows

    @property
    def nrows(self) -> int:
        """Number of rows in the table, excluding headers."""
        return len(self._rows)

    @property
    def ncols(self) -> int:
        """Number of columns in the table."""
        return len(self._rows[0])

    def _calc_max_cell_widths(self) -> List[int]:
        """
        Scans `rows` and `headers` to determine the maximum cell width
        for each column.
        """
        if self.headers is None:
            max_cell_widths = [1] * self.ncols
        else:
            max_cell_widths = [len(entry) + 2 for entry in self.headers]

        for row in self.rows:
            for ii in range(len(max_cell_widths)):
                max_cell_widths[ii] = max(max_cell_widths[ii], len(row[ii]) + 2)

        return max_cell_widths

    def auto_insert_horizontal_dividers(self, on_columns: List[int]):
        """
        Automatically insert horizontal dividers into the table based
        on cell value switching in columns specified by ``on_columns``.
        Cell "switching" corresponds to when a cell value switches from
        being empty to non-empty as moving down a column.  The
        horizontal divider will be inserted above the non-empty cell
        from the associated column to the end of the table.

        Parameters
        ----------
        on_columns : List[int]
            List of column indices to be used for determining where to
            insert the horizontal divider.
        """

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
        """
        Generate and return the string contain the table associated with
        `rows` and `headers`.
        """

        table_string = ""

        if self.headers is not None:
            for ii, entry in enumerate(self.headers):
                table_string += f"| {entry:<{self.cell_widths[ii] - 2}} "
            table_string += "|\n"

            for ii, entry in enumerate(self.headers):
                table_string += f"+{'-' * (self.cell_widths[ii])}"
            table_string += "+\n"

        rows = self.rows if self._rows_w_dividers is None else self._rows_w_dividers
        for row in rows:
            for ii, entry in enumerate(row):
                table_string += f"| {entry:<{self.cell_widths[ii] - 2}} "
            table_string += "|\n"

        return table_string
