"""Tests for tree-view sort keys without requiring a Tk display."""

import unittest

from modules import treeview_mod


class FakeTree:
    def __init__(self, values, tags):
        self.values = values
        self.tags = tags
        self.order = list(values)
        self.heading_command = None

    def get_children(self, _parent=''):
        return list(self.order)

    def set(self, child, column):
        return self.values[child][column]

    def move(self, child, _parent, index):
        self.order.remove(child)
        self.order.insert(index, child)

    def item(self, child, option=None, **kwargs):
        if kwargs:
            self.tags[child] = kwargs['tags']
        return self.tags[child] if option == 'tags' else None

    def heading(self, _column, **kwargs):
        self.heading_command = kwargs.get('command')


class TreeviewSortingTests(unittest.TestCase):
    def setUp(self):
        self.tree = FakeTree(
            values={
                'a': {'Tally number': '3014', 'File': 'zeta'},
                'b': {'Tally number': '10014', 'File': 'Alpha'},
                'c': {'Tally number': '4034', 'File': 'beta'},
                'd': {'Tally number': '14', 'File': 'Gamma'},
                'e': {'Tally number': 'N/A', 'File': 'delta'},
            },
            tags={
                'a': ('checked', 'evenrow'),
                'b': ('unchecked', 'oddrow'),
                'c': ('checked', 'oddrow'),
                'd': ('unchecked', 'evenrow'),
                'e': ('checked', 'oddrow'),
            },
        )

    def test_tally_numbers_sort_numerically(self):
        treeview_mod.sort_treeview_column(self.tree, 'Tally number', False)
        self.assertEqual(self.tree.order, ['d', 'a', 'c', 'b', 'e'])
        self.assertEqual(self.tree.tags['d'], ('unchecked', 'oddrow'))
        self.assertEqual(self.tree.tags['a'], ('checked', 'evenrow'))
        self.assertIsNotNone(self.tree.heading_command)

    def test_numeric_descending_keeps_non_numeric_values_at_end(self):
        treeview_mod.sort_treeview_column(self.tree, 'Tally number', True)
        self.assertEqual(self.tree.order, ['b', 'c', 'a', 'd', 'e'])

    def test_text_columns_remain_case_insensitive_text_sort(self):
        treeview_mod.sort_treeview_column(self.tree, 'File', False)
        self.assertEqual(self.tree.order, ['b', 'c', 'e', 'd', 'a'])


if __name__ == '__main__':
    unittest.main()
