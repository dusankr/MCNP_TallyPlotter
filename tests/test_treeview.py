"""Tests for tree-view sort keys without requiring a Tk display."""

import unittest
from unittest.mock import patch

from modules import config_mod, read_mod, treeview_mod
from modules.tally_data import Tally


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


class FakeRefreshTree:
    def __init__(self):
        self.rows = {}

    def get_children(self):
        return list(self.rows)

    def delete(self, key):
        del self.rows[key]

    def insert(self, _parent, index, iid, values, tags):
        self.rows[iid] = {'index': index, 'values': values, 'tags': tags}
        return iid


def tally(flux):
    return Tally(
        tally_num='4', tally_type=4, particle='neutrons', energy=[0.0, 1.0, 2.0],
        flux=flux, error=[0.0, 0.0, 0.0], cutoff_energy=0.0,
        flux_normalized=list(flux), nps=100,
    )


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

    def test_sort_preserves_zero_value_row_tag(self):
        self.tree.tags['a'] = ('checked', 'evenrow', 'zero_values')

        treeview_mod.sort_treeview_column(self.tree, 'Tally number', False)

        self.assertEqual(self.tree.tags['a'], ('zero_values', 'checked', 'evenrow'))


class ZeroValueTallyTests(unittest.TestCase):
    def test_zero_only_detection_ignores_cutoff_placeholder(self):
        self.assertTrue(tally([0.0, 0.0, -0.0]).has_only_zero_values)
        self.assertFalse(tally([0.0, 0.0, 1.0e-30]).has_only_zero_values)
        self.assertFalse(tally([0.0]).has_only_zero_values)

    def test_zero_energy_boundary_does_not_mark_nonzero_values_as_zero_only(self):
        self.assertFalse(tally([0.0, 2.0, 3.0]).has_only_zero_values)

    def test_tree_rows_with_only_zero_values_receive_red_status_tag(self):
        tree = FakeRefreshTree()
        tallies = {'zero_4': tally([0.0, 0.0, 0.0]), 'nonzero_4': tally([0.0, 0.0, 2.0])}

        with patch.object(config_mod, 'tallies', tallies):
            read_mod.refresh_tally_tree(tree)

        self.assertEqual(tree.rows['zero_4']['tags'], ('zero_values', 'unchecked', 'oddrow'))
        self.assertNotIn('zero_values', tree.rows['nonzero_4']['tags'])


if __name__ == '__main__':
    unittest.main()
