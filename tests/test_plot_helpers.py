import unittest

from modules import plot_mod


class FakeVariable:
    def __init__(self, name):
        self.name = name
        self.added = []
        self.removed = []

    def __eq__(self, other):
        return isinstance(other, FakeVariable) and self.name == other.name

    __hash__ = None

    def trace_add(self, mode, callback):
        trace_id = f"{self.name}-{len(self.added)}"
        self.added.append((mode, callback, trace_id))
        return trace_id

    def trace_remove(self, mode, trace_id):
        self.removed.append((mode, trace_id))


class PlotTraceTests(unittest.TestCase):
    def test_write_traces_support_unhashable_tk_style_variables(self):
        variables = [FakeVariable("first"), FakeVariable("second")]
        callback = object()
        handles = []

        plot_mod.add_write_traces(variables, callback, handles)
        plot_mod.add_write_traces(variables, callback, handles)

        self.assertEqual(len(handles), 2)
        self.assertEqual([len(variable.added) for variable in variables], [1, 1])

        plot_mod.remove_write_traces(handles)

        self.assertEqual(handles, [])
        self.assertEqual(variables[0].removed, [("write", "first-0")])
        self.assertEqual(variables[1].removed, [("write", "second-0")])


if __name__ == "__main__":
    unittest.main()
