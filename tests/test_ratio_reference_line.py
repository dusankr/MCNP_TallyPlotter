import unittest

from modules import plot_core


class FakeAxis:
    def __init__(self):
        self.calls = []

    def axhline(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class RatioReferenceLineTests(unittest.TestCase):
    def test_draws_thin_dashed_line_for_active_ratio_plot(self):
        axis = FakeAxis()

        plot_core.add_ratio_reference_line(
            axis, {"ratio": "reference_tally", "ratio_reference_line": True}
        )

        self.assertEqual(axis.calls, [
            ((1.0,), {"color": "black", "linestyle": "--", "linewidth": 0.75, "zorder": 3})
        ])

    def test_does_not_draw_for_non_ratio_or_disabled_option(self):
        axis = FakeAxis()

        plot_core.add_ratio_reference_line(axis, {"ratio": "no ratio", "ratio_reference_line": True})
        plot_core.add_ratio_reference_line(axis, {"ratio": "reference_tally", "ratio_reference_line": False})

        self.assertEqual(axis.calls, [])


if __name__ == "__main__":
    unittest.main()
