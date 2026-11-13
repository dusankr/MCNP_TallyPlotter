"""Legend labels in the main tree must match the persisted plot labels."""

from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import tomllib

from modules import config_mod, legend_tree_mod, read_mod, settings_mod
from modules.tally_data import Tally


def make_tally():
    return Tally('4', 4, 'neutrons', [0.0, 1.0], [0.0, 2.0],
                 [0.0, 0.1], 0.0, [0.0, 2.0], nps=100)


class FakeTree:
    def __init__(self):
        self.rows = {}

    def get_children(self, _parent=''):
        return list(self.rows)

    def delete(self, key):
        del self.rows[key]

    def insert(self, _parent, index, iid, values, tags):
        self.rows[iid] = {'values': values, 'tags': tags}

    def set(self, key, column, value):
        self.rows[key]['values'][2] = value


class LegendPersistenceTests(unittest.TestCase):
    def test_edit_persists_and_reload_restores_label(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'legend.toml'
            path.write_text('[legend]\nsource_4 = "Old"\n[other]\nvalue = 2\n', encoding='utf-8')
            tally = make_tally()
            with patch.object(config_mod, 'tallies', {'source_4': tally}):
                settings_mod.readsave_legend(path)
                tree = FakeTree()
                read_mod.refresh_tally_tree(tree)
                self.assertEqual(tree.rows['source_4']['values'][2], 'Old')

                self.assertEqual(settings_mod.update_tally_legend('source_4', '  New label  ', path),
                                 'New label')
                legend_tree_mod.refresh_legend_column(tree)
                self.assertEqual(tree.rows['source_4']['values'][2], 'New label')
                tally.legend_name = 'stale'
                settings_mod.readsave_legend(path)
                self.assertEqual(tally.legend_name, 'New label')

            with path.open('rb') as source:
                data = tomllib.load(source)
            self.assertEqual(data['legend']['source_4'], 'New label')
            self.assertEqual(data['other']['value'], 2)

    def test_invalid_edit_keeps_file_and_loaded_label(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'legend.toml'
            path.write_text('[legend]\nsource_4 = "Original"\n', encoding='utf-8')
            tally = make_tally()
            tally.legend_name = 'Original'
            with patch.object(config_mod, 'tallies', {'source_4': tally}):
                with self.assertRaises(ValueError):
                    settings_mod.update_tally_legend('source_4', '  ', path)
                self.assertEqual(tally.legend_name, 'Original')
                self.assertIn('Original', path.read_text(encoding='utf-8'))


class LegendCellInteractionTests(unittest.TestCase):
    def test_double_click_edits_only_legend_cell(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f'Tk is unavailable: {exc}')
        self.addCleanup(root.destroy)
        root.geometry('420x160+20000+20000')
        tree = ttk.Treeview(root, columns=('File', 'Legend'), show='headings')
        tree.heading('File', text='File')
        tree.heading('Legend', text='Legend')
        tree.column('File', width=150)
        tree.column('Legend', width=200)
        tree.insert('', 'end', iid='source_4', values=('source', 'Original'))
        tree.pack(fill='both', expand=True)
        root.update()
        bounds = tree.bbox('source_4', 'Legend')
        self.assertTrue(bounds)
        event = SimpleNamespace(x=bounds[0] + 5, y=bounds[1] + 5)

        tally = make_tally()
        tally.legend_name = 'Original'
        real_update = settings_mod.update_tally_legend
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(config_mod, 'tallies', {'source_4': tally}), \
                patch.object(settings_mod, 'update_tally_legend',
                             side_effect=lambda key, name: real_update(
                                 key, name, Path(directory) / 'legend.toml')):
            self.assertTrue(legend_tree_mod.edit_legend_from_event(event, tree))
            editor = next(child for child in tree.winfo_children()
                          if isinstance(child, ttk.Entry))
            root.update()
            editor.delete(0, tk.END)
            editor.insert(0, 'Edited')
            editor.event_generate('<Return>', when='now')
            root.update()
            self.assertEqual(tree.set('source_4', 'Legend'), 'Edited')
            self.assertEqual(tally.legend_name, 'Edited')
            self.assertFalse(legend_tree_mod.edit_legend_from_event(
                SimpleNamespace(x=5, y=bounds[1] + 5), tree))
