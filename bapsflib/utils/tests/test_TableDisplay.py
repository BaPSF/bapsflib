import unittest as ut

from bapsflib.utils import TableDisplay


class TestTableDisplay(ut.TestCase):

    def test_raises(self):
        cases = [
            # (_raises, rows, headers)
            (TypeError, "not a list", None),
            (TypeError, None, None),
            (TypeError, ["not a list of lists"], None),
            (TypeError, [["one", "two"], ["three", "four"]], "not None or a list"),
            # all contents of rows need to be strings
            (ValueError, [["one", "two"], ["three", 4]], None),
            # not equal columns between rows and headers
            (ValueError, [["one", "two"], ["three", "four"]], ["col_1"]),
            # all contents of headers need to be strings
            (ValueError, [["one", "two"], ["three", "four"]], ["col_1", 2]),
        ]
        for _raises, rows, headers in cases:
            with self.subTest(_raises=_raises, rows=rows, headers=headers):
                self.assertRaises(
                    _raises,
                    TableDisplay,
                    rows=rows,
                    headers=headers,
                )

    def test_simple_table(self):
        rows = [
            ["one", "two", "three"],
            ["four", "five", "six"],
            ["seven", "eight", "nine"],
        ]
        expected = (
            "| one   | two   | three |\n"
            "| four  | five  | six   |\n"
            "| seven | eight | nine  |\n"
        )

        td = TableDisplay(rows)
        self.assertEqual(td.table_string(), expected)

    def test_simple_table_w_headers(self):
        rows = [
            ["one", "two", "three"],
            ["four", "five", "six"],
            ["seven", "eight", "nine"],
        ]
        headers = ["col1", "col2", "col3"]
        expected = (
            "| col1  | col2  | col3  |\n"
            "+-------+-------+-------+\n"
            "| one   | two   | three |\n"
            "| four  | five  | six   |\n"
            "| seven | eight | nine  |\n"
        )

        td = TableDisplay(rows, headers)
        self.assertEqual(td.table_string(), expected)

    def test_cell_widths(self):
        cases = [
            # (rows, headers, expected_wdiths)
            ([["one", "two", "three"]], None, [5, 5, 7]),
            ([["one", "two", "three"]], ["col1", "2", "Really long"], [6, 5, 13]),
            (
                [["one", "eight", "three"], ["elephant", "ant", "fish"]],
                None,
                [10, 7, 7],
            ),
            (
                [["one", "eight", "three"], ["elephant", "ant", "fish"]],
                ["col1", "2", "Really long"],
                [10, 7, 13],
            ),
        ]
        for rows, headers, expected in cases:
            with self.subTest(rows=rows, headers=headers, expected=expected):
                tb = TableDisplay(rows, headers)
                self.assertEqual(tb.cell_widths, expected)

    def test_nrows(self):
        cases = [
            # (rows, headers, nrows)
            ([["one", "two", "three"]], None, 1),
            ([["one", "two", "three"], ["four", "five", "six"]], None, 2),
            ([["one", "two", "three"]], ["1", "2", "3"], 1),
            ([["one", "two", "three"], ["four", "five", "six"]], ["1", "2", "3"], 2),
        ]
        for rows, headers, nrows in cases:
            with self.subTest(rows=rows, headers=headers, nrows=nrows):
                tb = TableDisplay(rows, headers)
                self.assertEqual(tb.nrows, nrows)

    def test_ncols(self):
        cases = [
            # (rows, headers, ncols)
            ([["one", "two", "three"]], None, 3),
            ([["one", "two", "three"], ["four", "five", "six"]], None, 3),
            ([["one", "two", "three"]], ["1", "2", "3"], 3),
            ([["one", "two", "three"], ["four", "five", "six"]], ["1", "2", "3"], 3),
            ([["one",]], None, 1),
            ([["one", "two"]], None, 2),
        ]
        for rows, headers, ncols in cases:
            with self.subTest(rows=rows, headers=headers, ncols=ncols):
                tb = TableDisplay(rows, headers)
                self.assertEqual(tb.ncols, ncols)
