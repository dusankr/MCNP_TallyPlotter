import unittest
from types import SimpleNamespace
from unittest.mock import patch

from modules import config_mod, tally_table_mod


def make_tally():
    return SimpleNamespace(
        energy=[0.0, 0.1, 1.0],
        flux=[0.0, 2.0, 4.0],
        error=[0.0, 0.1, 0.2],
        flux_normalized=[0.0, 20.0, 4.44444444],
        total=6.0,
        total_error=0.15,
    )


class FakeTreeview:
    def __init__(self, region="cell", row="sample.o:14"):
        self.region = region
        self.row = row

    def identify_region(self, _x, _y):
        return self.region

    def identify_row(self, _y):
        return self.row


class TallyTableTests(unittest.TestCase):
    def test_tally_value_rows_excludes_artificial_first_values_and_adds_total(self):
        self.assertEqual(
            tally_table_mod.tally_value_rows(make_tally()),
            [
                (0.1, 2.0, 0.1, 20.0),
                (1.0, 4.0, 0.2, 4.44444444),
                ("Total", 6.0, 0.15, None),
            ],
        )

    def test_tally_value_rows_omits_missing_total(self):
        tally = make_tally()
        tally.total = None

        self.assertEqual(len(tally_table_mod.tally_value_rows(tally)), 2)

    def test_double_click_opens_clicked_tally(self):
        tally = make_tally()
        event = SimpleNamespace(x=20, y=30)
        parent = object()
        config_mod.tallies["sample.o:14"] = tally

        try:
            with patch.object(
                tally_table_mod, "open_tally_values_window", return_value="window"
            ) as opener:
                result = tally_table_mod.open_tally_table_from_event(
                    event, FakeTreeview(), parent
                )
        finally:
            config_mod.tallies.pop("sample.o:14", None)

        self.assertEqual(result, "window")
        opener.assert_called_once_with(parent, "sample.o:14", tally)

    def test_double_click_ignores_heading_and_unknown_rows(self):
        event = SimpleNamespace(x=20, y=30)

        with patch.object(tally_table_mod, "open_tally_values_window") as opener:
            self.assertIsNone(
                tally_table_mod.open_tally_table_from_event(
                    event, FakeTreeview(region="heading"), object()
                )
            )
            self.assertIsNone(
                tally_table_mod.open_tally_table_from_event(
                    event, FakeTreeview(row="missing"), object()
                )
            )

        opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
