"""F8 input rows must be retained independently of later plotting choices."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules import config_mod, read_mod


class F8ReaderTests(unittest.TestCase):
    def test_single_and_multiple_cells_keep_first_two_reported_rows(self):
        for cell_count in (1, 2):
            with self.subTest(cell_count=cell_count), tempfile.TemporaryDirectory() as directory, \
                    patch.object(config_mod, 'tallies', {}):
                path = Path(directory) / 'pulse.o'
                text = '1tally 18 nps = 1000000\n tally type 8\n particle(s): photons\n'
                for cell in range(1, cell_count + 1):
                    text += (f' cell {cell}\n energy\n'
                             f' 0.0000E+00 {2 * cell}.0 0.1\n'
                             f' 1.0000E-12 {3 * cell}.0 0.2\n'
                             f' 1.0000E+00 {4 * cell}.0 0.3\n'
                             f' total {9 * cell}.0 0.12\n\n')
                path.write_text(text + ' end\n', encoding='utf-8')
                read_mod.read_tally(path.parent, path)
                expected_keys = (['pulse_18'] if cell_count == 1 else
                                 ['pulse_18_cell_1', 'pulse_18_cell_2'])
                self.assertEqual(list(config_mod.tallies), expected_keys)
                for cell, key in enumerate(expected_keys, start=1):
                    tally = config_mod.tallies[key]
                    self.assertEqual(tally.tally_type, 8)
                    self.assertEqual(tally.energy[1:], [0, 1e-12, 1])
                    self.assertEqual(tally.flux[1:], [2 * cell, 3 * cell, 4 * cell])
                    self.assertEqual(tally.error[1:], [.1, .2, .3])
                    self.assertEqual(tally.total, 9 * cell)
