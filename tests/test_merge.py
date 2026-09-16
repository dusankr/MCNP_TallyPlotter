"""Regression tests for tally merging and output-file round trips."""

import copy
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from modules import config_mod, merge_mod, read_mod
from modules.tally_data import Tally


def tally(**changes):
    args = dict(tally_num='4', tally_type=4, particle='neutrons',
                energy=[0.0, 0.1, 1.0], flux=[0.0, 2.0, 3.0],
                error=[0.0, 0.1, 0.2], cutoff_energy=0.0,
                flux_normalized=[0.0, 20.0, 3.0 / 0.9],
                nps=1000000, total=5.0, total_error=0.12)
    args.update(changes)
    return Tally(**args)


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.state = patch.multiple(config_mod, tallies={}, output_files=[], non_output=[])
        self.state.start()
        self.addCleanup(self.state.stop)

    def test_raw_sum_and_errors_for_three_inputs(self):
        inputs = [('a_4', tally()), ('b_14', tally(tally_num='14')),
                  ('c_24', tally(tally_num='24'))]
        before = copy.deepcopy([t.__dict__ for _, t in inputs])
        result = merge_mod.merge_tallies(inputs)
        self.assertEqual(result.flux, [0.0, 6.0, 9.0])
        self.assertAlmostEqual(result.error[1], 0.1 / math.sqrt(3))
        self.assertAlmostEqual(result.error[2], 0.2 / math.sqrt(3))
        self.assertEqual(result.nps, 1000000)
        self.assertEqual(result.total, 15.0)
        self.assertAlmostEqual(result.total_error, 0.12 / math.sqrt(3))
        self.assertEqual(result.checks_passed, 'N/A')
        self.assertEqual([t.__dict__ for _, t in inputs], before)

    def test_validation_creates_no_file(self):
        variants = [dict(nps=None), dict(nps=2), dict(particle='photons'),
                    dict(tally_type=5), dict(flux=[0, 2]), dict(error=[0, 0.1]),
                    dict(energy=[0, 0.10000000000000002, 1]),
                    dict(energy=[0.001, 0.1, 1]), dict(flux=[0, float('nan'), 3]),
                    dict(error=[0, -0.1, 0.2]), dict(total=None)]
        for changes in variants:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    merge_mod.save_merged_tally([('a', tally()), ('b', tally(**changes))], self.directory)
                self.assertEqual(list(self.directory.iterdir()), [])
        for selected in ([], [('a', tally())], [('a', tally()), ('a', tally())]):
            with self.assertRaises(ValueError):
                merge_mod.save_merged_tally(selected, self.directory)

    def test_signed_sum_propagates_nonnegative_relative_error(self):
        result = merge_mod.merge_tallies([
            ('a', tally()), ('b', tally(flux=[0, -4, -6], total=-10))])
        self.assertEqual(result.flux, [0, -2, -3])
        self.assertAlmostEqual(result.error[2], math.hypot(0.6, 1.2) / 3)

    def test_zero_cancellation_with_uncertainty_is_rejected(self):
        for normalize in (False, True):
            with self.subTest(normalize=normalize), self.assertRaisesRegex(ValueError, 'zero.*uncertainty'):
                merge_mod.save_merged_tally([
                    ('a', tally()), ('b', tally(flux=[0, -2, -6], total=-8))],
                    self.directory, normalize_by_nps=normalize)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_all_zero_bins_are_valid_in_both_modes(self):
        for normalize in (False, True):
            result = merge_mod.merge_tallies([
                ('a', tally(flux=[0, 0, 0], error=[0, 0, 0], total=0, total_error=0)),
                ('b', tally(flux=[0, 0, 0], error=[0, 0, 0], total=0, total_error=0))],
                normalize_by_nps=normalize)
            self.assertEqual(result.flux, [0, 0, 0])
            self.assertEqual(result.error, [0, 0, 0])
            self.assertEqual(result.total_error, 0)

    @staticmethod
    def tally_from_history_scores(scores):
        """Independent oracle: compute MCNP means/errors directly from history scores."""
        def statistics(values):
            mean = math.fsum(values) / len(values)
            sigma = math.sqrt(math.fsum((v - mean) ** 2 for v in values)) / len(values)
            return mean, sigma / abs(mean) if mean else 0
        bins = [statistics(column) for column in zip(*scores)]
        total, total_error = statistics([sum(row) for row in scores])
        return tally(nps=len(scores), flux=[0] + [v for v, _ in bins],
                     error=[0] + [r for _, r in bins], total=total, total_error=total_error)

    def test_nps_normalization_matches_pooled_history_scores(self):
        score_groups = [[[0, 1], [2, 3]], [[1, 0], [0, 4], [3, 0]],
                        [[1, 2], [3, 4], [2, 0], [0, 0]]]
        inputs = [(str(i), self.tally_from_history_scores(scores))
                  for i, scores in enumerate(score_groups)]
        expected = self.tally_from_history_scores([row for scores in score_groups for row in scores])
        result = merge_mod.merge_tallies(inputs, normalize_by_nps=True)
        self.assertEqual(result.nps, 9)
        for attribute in ('flux', 'error'):
            for actual, target in zip(getattr(result, attribute), getattr(expected, attribute)):
                self.assertAlmostEqual(actual, target, places=14)
        self.assertAlmostEqual(result.total, expected.total)
        self.assertAlmostEqual(result.total_error, expected.total_error)
        # Equal zero errors in different constant runs still give pooled spread.
        constants = [('a', tally(nps=2, flux=[0, 1, 1], error=[0, 0, 0])),
                     ('b', tally(nps=3, flux=[0, 3, 3], error=[0, 0, 0]))]
        pooled = merge_mod.merge_tallies(constants, normalize_by_nps=True)
        self.assertAlmostEqual(pooled.flux[1], 2.2)
        self.assertAlmostEqual(pooled.error[1], math.sqrt(0.192) / 2.2)

    def test_equal_nps_modes_have_different_mean_and_nps(self):
        sources = [('a', tally()), ('b', tally())]
        summed = merge_mod.merge_tallies(sources)
        pooled = merge_mod.merge_tallies(sources, normalize_by_nps=True)
        self.assertEqual(summed.flux, [0, 4, 6])
        self.assertEqual(pooled.flux, [0, 2, 3])
        self.assertEqual(summed.nps, 1000000)
        self.assertEqual(pooled.nps, 2000000)
        self.assertAlmostEqual(pooled.error[1], 0.1 / math.sqrt(2))

    def test_normalized_output_round_trip_and_sequential_merge(self):
        sources = [('a', self.tally_from_history_scores([[0, 1], [2, 3]])),
                   ('b', self.tally_from_history_scores([[1, 0], [0, 4], [3, 0]])),
                   ('c', self.tally_from_history_scores([[2, 1], [1, 4]]))]
        path, first = merge_mod.save_merged_tally(sources[:2], self.directory, normalize_by_nps=True)
        self.assertTrue(path.name.endswith('_NPSnorm.o'))
        self.assertIn('NPS-normalized', path.read_text())
        read_mod.read_tally(self.directory, path)
        loaded = config_mod.tallies[f'{path.stem}_4']
        self.assertEqual(loaded.nps, 5)
        self.assertEqual(loaded.flux, first.flux)
        self.assertEqual(loaded.error, first.error)
        sequential = merge_mod.merge_tallies([('pooled', loaded), sources[2]], normalize_by_nps=True)
        together = merge_mod.merge_tallies(sources, normalize_by_nps=True)
        self.assertEqual(sequential.nps, together.nps)
        for attr in ('flux', 'error'):
            for actual, target in zip(getattr(sequential, attr), getattr(together, attr)):
                self.assertAlmostEqual(actual, target, places=14)
        self.assertAlmostEqual(sequential.total_error, together.total_error)

    def test_normalized_mode_still_checks_compatibility(self):
        for changes in [dict(nps=None), dict(nps=0), dict(nps=-1), dict(particle='photons'),
                        dict(tally_type=5), dict(flux=[0, 2]), dict(energy=[0, 0.2, 1])]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                merge_mod.save_merged_tally([('a', tally()), ('b', tally(**changes))],
                                            self.directory, normalize_by_nps=True)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_output_survives_restart_and_can_be_merged_again(self):
        for particle, cutoff, energies in [('neutrons', 0.0, [0.0, 0.1, 1.0]),
                                            ('photons', 0.01, [0.01, 0.1, 1.0]),
                                            ('photons', 0.1, [0.0, 0.01, 1.0])]:
            with self.subTest(particle=particle, cutoff=cutoff):
                source = tally(particle=particle, cutoff_energy=cutoff, energy=energies)
                path, merged = merge_mod.save_merged_tally([('a', source), ('b', source)], self.directory)
                self.assertRegex(path.name, r'^merged_\d{8}_\d{6}_\d{6}\.o$')
                config_mod.tallies.clear()
                read_mod.read_tally(self.directory, path)
                self.assertNotIn(path.name, config_mod.non_output)
                loaded = config_mod.tallies[f'{path.stem}_4']
                for attr in ('energy', 'flux', 'error', 'flux_normalized', 'nps', 'total',
                             'total_error', 'particle', 'tally_type', 'cutoff_energy', 'comment'):
                    self.assertEqual(getattr(loaded, attr), getattr(merged, attr), attr)
                again = merge_mod.merge_tallies([('merged', loaded), ('original', source)])
                self.assertEqual(again.flux, [0, 6, 9])

    def test_nps_parser_uses_actual_tally_header(self):
        for token, expected in [('10000000000000001', 10000000000000001),
                                ('1.0E+06', 1000000), ('1D6', 1000000),
                                ('NaN', None), ('Infinity', None), ('0', None),
                                ('-1', None), ('1.5', None), ('***', None)]:
            self.assertEqual(read_mod.parse_tally_nps(f'1tally 4 nps = {token}'), expected)
        self.assertIsNone(read_mod.parse_tally_nps('nps 1000000'))

    def test_timestamp_collision_does_not_overwrite_existing_file(self):
        from datetime import datetime
        with patch.object(merge_mod, 'datetime') as clock:
            clock.now.return_value = datetime(2026, 9, 16, 12, 30)
            path, _ = merge_mod.save_merged_tally([('a', tally()), ('b', tally())], self.directory)
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                merge_mod.save_merged_tally([('c', tally()), ('d', tally())], self.directory)
            self.assertEqual(path.read_bytes(), original)

    def test_reader_allows_plotting_when_merge_metadata_is_missing(self):
        path = self.directory / 'unknown.o'
        path.write_text('1tally 4\n tally type 4\n particle(s): neutrons\n'
                        ' cell 1\n energy\n 0.1 2 0.1\n 1.0 3 0.2\n total ***** *****\n',
                        encoding='utf-8')
        read_mod.read_tally(self.directory, path)
        loaded = config_mod.tallies['unknown_4']
        self.assertEqual(loaded.flux, [0, 2, 3])
        self.assertIsNone(loaded.nps)
        self.assertIsNone(loaded.total)
        with self.assertRaisesRegex(ValueError, 'NPS'):
            merge_mod.merge_tallies([('a', loaded), ('b', tally())])

    def test_reader_keeps_nps_and_totals_for_each_cell(self):
        path = self.directory / 'source.o'
        path.write_text('1tally 14 nps = 1000000\n'
                        ' tally type 4\n particle(s): neutrons\n cell 1\n energy\n'
                        ' 0.1 2.0 0.1\n 1.0 3.0 0.2\n total 5.0 0.12\n\n'
                        ' cell 2\n energy\n'
                        ' 0.1 4.0 0.2\n 1.0 5.0 0.3\n total 9.0 0.23\n\n'
                        ' end\n', encoding='utf-8')
        read_mod.read_tally(self.directory, path)
        self.assertEqual(set(config_mod.tallies), {'source_14_cell_1', 'source_14_cell_2'})
        self.assertEqual(config_mod.tallies['source_14_cell_1'].total, 5)
        self.assertEqual(config_mod.tallies['source_14_cell_2'].total, 9)
        self.assertTrue(all(t.nps == 1000000 for t in config_mod.tallies.values()))
        tree = Mock()
        tree.get_children.return_value = []
        read_mod.refresh_tally_tree(tree)
        self.assertEqual([call.kwargs['iid'] for call in tree.insert.call_args_list],
                         ['source_14_cell_1', 'source_14_cell_2'])

    def test_button_warns_and_does_not_write_for_invalid_selection(self):
        tree = Mock()
        tree.get_checked.return_value = ['a', 'b']
        config_mod.tallies.update(a=tally(), b=tally(nps=2))
        with patch.object(merge_mod, 'messagebox') as dialogs:
            merge_mod.merge_selected_tallies(tree)
        dialogs.showwarning.assert_called_once()
        dialogs.showinfo.assert_not_called()
        tree.insert.assert_not_called()
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_button_saves_and_selects_new_row(self):
        tree = Mock()
        tree.get_checked.return_value = ['a', 'b']
        tree.get_children.return_value = []
        config_mod.tallies.update(a=tally(), b=tally())
        with patch.dict(config_mod.plot_settings, work_dir_path=self.directory), \
                patch.object(merge_mod, 'messagebox') as dialogs, \
                patch.object(merge_mod.settings_mod, 'readsave_legend'):
            merge_mod.merge_selected_tallies(tree)
        dialogs.showinfo.assert_called_once()
        self.assertEqual(len(config_mod.tallies), 3)
        self.assertEqual(len(list(self.directory.glob('merged_*.o'))), 1)
        key = f'{config_mod.output_files[0].stem}_4'
        tree.change_state.assert_called_once_with(key, 'checked')

    def test_button_passes_normalized_mode_and_accepts_unequal_nps(self):
        tree = Mock()
        tree.get_checked.return_value = ['a', 'b']
        tree.get_children.return_value = []
        config_mod.tallies.update(a=tally(nps=100), b=tally(nps=300, flux=[0, 4, 6], total=10))
        with patch.dict(config_mod.plot_settings, work_dir_path=self.directory), \
                patch.object(merge_mod, 'messagebox') as dialogs, \
                patch.object(merge_mod.settings_mod, 'readsave_legend'):
            merge_mod.merge_selected_tallies(tree, normalize_by_nps=True)
        dialogs.showinfo.assert_called_once()
        dialogs.showwarning.assert_not_called()
        output = config_mod.output_files[0]
        self.assertTrue(output.name.endswith('_NPSnorm.o'))
        merged = config_mod.tallies[f'{output.stem}_4']
        self.assertEqual(merged.nps, 400)
        self.assertEqual(merged.flux, [0, 3.5, 5.25])


if __name__ == '__main__':
    unittest.main()
