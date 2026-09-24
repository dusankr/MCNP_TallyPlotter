"""Sum source contributions or pool histories using MCNP tally statistics.

See doc/tally_merge.md for the manual references, formulas, and assumptions.
"""

import math
import re
from collections import defaultdict
from pathlib import Path
from tkinter import messagebox

from modules import config_mod, read_mod, settings_mod
from modules.tally_data import Tally


def _split_tally_key(key, tally):
    """Return the source-file stem and an optional cell/surface item suffix."""
    match = re.match(
        rf'^(?P<source>.+)_{re.escape(str(tally.tally_num))}'
        r'(?P<item>_[^_]+_\d+)?$', key,
    )
    if match is None:
        return key, ''
    return match.group('source'), (match.group('item') or '').lstrip('_')


def _is_previously_merged(tally):
    """Do not include prior generated results in a new batch and double-count them."""
    return tally.comment.startswith(('Merged source sum:', 'Merged NPS-normalized:'))


def _file_preamble(description, error_description):
    return [
        'MCNP TallyPlotter merged tally output (postprocessed)\n',
        description,
        error_description,
        'Original MCNP statistical checks are not applicable to this merged tally.\n',
        'particle energy cutoffs                                     print table 101\n',
        '\n', '\n', '\n', '\n', '\n',
    ]


def _tally_data_lines(merged, item=''):
    """Serialize one tally's data table, optionally retaining a cell/surface item."""
    if item:
        item_name, item_number = item.rsplit('_', 1)
        item_line = f' {item_name} {item_number}\n'
    else:
        item_line = ' cell 1\n'
    lines = [
        item_line,
        ' energy         tally         relative error\n',
    ]
    for energy, value, error in zip(merged.energy[1:], merged.flux[1:], merged.error[1:]):
        lines.append(f' {energy:.17e} {value:.17e} {error:.17e}\n')
    lines.extend([f' total {merged.total:.17e} {merged.total_error:.17e}\n', '\n'])
    return lines


def _tally_header_lines(merged, comment=None):
    return [
        f'1tally {merged.tally_num}       nps = {merged.nps}\n',
        '+ ' + (comment or merged.comment).replace('\n', ' ').replace('\r', ' ') + '\n',
        f' tally type {merged.tally_type}\n',
        f' particle(s): {merged.particle}\n',
    ]


def _combine_with_error(values, errors, histories=None):
    """Add independent means, or reconstruct pooled MCNP history statistics."""
    if histories is None:
        total = math.fsum(values)
        sigma = math.hypot(*(value * error for value, error in zip(values, errors)))
    else:
        nps = sum(histories)
        weights = [count / nps for count in histories]
        total = math.fsum(weight * value for weight, value in zip(weights, values))
        # Equivalent to pooling first/second history moments (MCNP eq. 2.226b).
        # The centered form avoids subtracting nearly equal second moments.
        within = [weight * value * error
                  for weight, value, error in zip(weights, values, errors)]
        between = [math.sqrt(weight / nps) * (value - total)
                   for weight, value in zip(weights, values)]
        sigma = math.hypot(*within, *between)
    if total == 0 and sigma != 0:
        raise ValueError('A merged bin or total is zero but has nonzero uncertainty. '
                         'Its relative error cannot be represented in the output file.')
    return total, sigma / abs(total) if total else 0.0


def merge_tallies(named_tallies, normalize_by_nps=False):
    """Validate all inputs before summing; leave the source tallies untouched."""
    if len(named_tallies) < 2:
        raise ValueError('Check at least two tallies to merge.')
    if len({name for name, _ in named_tallies}) != len(named_tallies):
        raise ValueError('The same tally cannot be selected more than once.')

    reference_name, reference = named_tallies[0]
    for name, tally in named_tallies:
        if not isinstance(tally.nps, int) or isinstance(tally.nps, bool) or tally.nps <= 0:
            raise ValueError(f'{name}: NPS is missing or invalid; merge statistics cannot be verified.')
        if not normalize_by_nps and tally.nps != reference.nps:
            raise ValueError(f'NPS differs: {reference_name} has {reference.nps}, {name} has {tally.nps}.')
        if tally.tally_type != reference.tally_type:
            raise ValueError(f'Tally types differ: {reference_name} and {name}.')
        if tally.particle.lower().removesuffix('s') != reference.particle.lower().removesuffix('s'):
            raise ValueError(f'Particles differ: {reference_name} and {name}.')
        if not (len(tally.energy) == len(tally.flux) == len(tally.error) == len(reference.flux)):
            raise ValueError(f'{name}: number of values or energy bins differs.')
        if tally.energy != reference.energy:
            raise ValueError(f'Energy bin boundaries differ: {reference_name} and {name}.')
        if len(tally.energy) < 2 or tally.flux[0] != 0 or tally.error[0] != 0:
            raise ValueError(f'{name}: missing energy-bin data or invalid leading placeholder.')
        if any(not math.isfinite(value) for value in tally.energy + tally.flux + tally.error):
            raise ValueError(f'{name}: data contains non-finite values.')
        if any(error < 0 for error in tally.error):
            raise ValueError(f'{name}: relative errors must be nonnegative.')
        if any(right < left for left, right in zip(tally.energy, tally.energy[1:])):
            raise ValueError(f'{name}: energy boundaries are not ordered.')
        if (tally.total is None or tally.total_error is None
                or not math.isfinite(tally.total) or not math.isfinite(tally.total_error)
                or tally.total_error < 0 or not math.isfinite(tally.cutoff_energy)):
            raise ValueError(f'{name}: missing or invalid total/error or cutoff data.')

    tallies = [tally for _, tally in named_tallies]
    histories = [t.nps for t in tallies] if normalize_by_nps else None
    flux, errors = [], []
    for index in range(len(reference.flux)):
        value, error = _combine_with_error([t.flux[index] for t in tallies],
                                           [t.error[index] for t in tallies], histories)
        flux.append(value)
        errors.append(error)
    total, total_error = _combine_with_error([t.total for t in tallies],
                                            [t.total_error for t in tallies], histories)
    normalized = read_mod.flux_norm(reference.energy, flux)
    if any(not math.isfinite(value) for value in flux + errors + normalized + [total, total_error]):
        raise ValueError('The merged values or uncertainties exceed the supported numeric range.')

    return Tally(
        tally_num=reference.tally_num, tally_type=reference.tally_type,
        particle=reference.particle, energy=list(reference.energy), flux=flux,
        error=errors, cutoff_energy=reference.cutoff_energy, flux_normalized=normalized,
        comment=('Merged NPS-normalized: ' if normalize_by_nps else 'Merged source sum: ')
                + ', '.join(f'{name} (NPS={t.nps})' for name, t in named_tallies),
        nps=sum(histories) if normalize_by_nps else reference.nps,
        total=total, total_error=total_error,
    )


def save_merged_tally(named_tallies, directory, normalize_by_nps=False):
    """Write a new output exclusively, after validating the selected merge mode."""
    merged = merge_tallies(named_tallies, normalize_by_nps=normalize_by_nps)
    if normalize_by_nps:
        description = 'NPS-normalized mean = sum(NPS_i * value_i) / sum(NPS_i); NPS summed.\n'
        error_description = 'MCNP pooled-history errors; assumes independent, non-overlapping histories.\n'
    else:
        description = 'Per-history source contributions summed; common NPS retained, no averaging.\n'
        error_description = 'Independent-source uncertainty propagation; common NPS is not pooled histories.\n'
    # 17 significant digits preserve float values and exact bin boundaries on reload.
    lines = _file_preamble(description, error_description)
    lines.extend([
        f' 1 0 {merged.particle.removesuffix("s")} {merged.cutoff_energy:.17e}\n',
        '\n',
    ])
    lines.extend(_tally_header_lines(merged))
    lines.extend(_tally_data_lines(merged))
    lines.append(' end of merged tally\n')
    suffix = '_NPSnorm' if normalize_by_nps else ''
    source_items = [_split_tally_key(key, tally) for key, tally in named_tallies]
    source_names = [source for source, _ in source_items]
    item_suffix = f'_{source_items[0][1]}' if source_items and all(
        item == source_items[0][1] for _, item in source_items
    ) and source_items[0][1] else ''
    output = Path(directory) / f'{"+".join(source_names)}_{merged.tally_num}{item_suffix}{suffix}.o'
    # Keep existing files intact when the same sources are merged again.
    with output.open('x', encoding='utf-8') as stream:
        try:
            stream.writelines(lines)
            stream.flush()
        except OSError:
            stream.close()
            output.unlink()
            raise
    return output, merged


def _batch_group_key(key, tally):
    """Fields that must match before source-sum tally values can be combined."""
    _, item = _split_tally_key(key, tally)
    return (
        tally.tally_num,
        item,
        tally.tally_type,
        tally.particle.lower().removesuffix('s'),
        tally.nps,
        tuple(tally.energy),
        tally.cutoff_energy,
    )


def _validate_batch_output_entries(entries):
    """Reject ambiguous repeated tally numbers that cannot reload from one file."""
    by_number = defaultdict(list)
    for entry in entries:
        by_number[entry['merged'].tally_num].append(entry)

    usable = []
    failures = []
    for tally_number, members in by_number.items():
        metadata = {
            (member['merged'].tally_type, member['merged'].particle, member['merged'].nps)
            for member in members
        }
        items = [member['item'] for member in members]
        if len(metadata) > 1:
            failures.append(
                f'Tally {tally_number}: incompatible type, particle, or NPS prevents one-file output.'
            )
        elif len(members) > 1 and (not all(items) or len(set(items)) != len(items)):
            failures.append(
                f'Tally {tally_number}: repeated tally items cannot be uniquely represented in one file.'
            )
        else:
            usable.extend(members)
    return usable, failures


def save_batch_merged_tallies(entries, directory):
    """Save multiple compatible merged tally blocks in one reloadable output file."""
    if not entries:
        raise ValueError('No merged tally groups are available for batch output.')

    source_names = []
    for entry in entries:
        for key, tally in entry['named_tallies']:
            source_name, _ = _split_tally_key(key, tally)
            if source_name not in source_names:
                source_names.append(source_name)
    output = Path(directory) / f'{"+".join(source_names)}_batch_merged.o'

    first = entries[0]['merged']
    lines = _file_preamble(
        'Batch source-sum tally merge; each tally keeps its common NPS.\n',
        'Independent-source uncertainty propagation; no averaging or multiplier applied.\n',
    )
    lines.extend([f' 1 0 {first.particle.removesuffix("s")} {first.cutoff_energy:.17e}\n', '\n'])

    for index, entry in enumerate(entries):
        merged = entry['merged']
        if index:
            lines.append('\n')
        lines.extend(_tally_header_lines(merged))
        lines.extend(_tally_data_lines(merged, entry['item']))
    lines.append(' end of merged tally batch\n')

    with output.open('x', encoding='utf-8') as stream:
        try:
            stream.writelines(lines)
            stream.flush()
        except OSError:
            stream.close()
            output.unlink()
            raise
    return output


def batch_merge_tallies(directory):
    """Merge every compatible default-mode group from the currently loaded tallies.

    A group needs at least two original tallies. Existing generated merge files are
    deliberately omitted so rerunning batch merge cannot include prior sums.
    """
    groups = defaultdict(list)
    skipped_merged = 0
    for key, tally in config_mod.tallies.items():
        if _is_previously_merged(tally):
            skipped_merged += 1
            continue
        groups[_batch_group_key(key, tally)].append((key, tally))

    completed = []
    failures = []
    unmatched = 0
    for named_tallies in groups.values():
        if len(named_tallies) < 2:
            unmatched += len(named_tallies)
            continue
        try:
            _, item = _split_tally_key(*named_tallies[0])
            completed.append({'named_tallies': named_tallies,
                              'merged': merge_tallies(named_tallies), 'item': item})
        except (ValueError, OverflowError) as exc:
            failures.append(f'{", ".join(key for key, _ in named_tallies)}: {exc}')

    completed, representation_failures = _validate_batch_output_entries(completed)
    failures.extend(representation_failures)
    if not completed:
        return None, [], unmatched, skipped_merged, failures
    try:
        output = save_batch_merged_tallies(completed, directory)
    except OSError as exc:
        failures.append(str(exc))
        return None, [], unmatched, skipped_merged, failures
    return output, completed, unmatched, skipped_merged, failures


def merge_selected_tallies(treeview, normalize_by_nps=False):
    """Main-window button action; validation failures never create a file."""
    selected = list(treeview.get_checked())
    try:
        named_tallies = [(key, config_mod.tallies[key]) for key in selected]
        output, merged = save_merged_tally(named_tallies, config_mod.plot_settings['work_dir_path'],
                                          normalize_by_nps=normalize_by_nps)
    except (ValueError, OverflowError, KeyError) as exc:
        messagebox.showwarning('Cannot merge tallies', str(exc))
        return
    except FileExistsError as exc:
        messagebox.showwarning('Merged file already exists',
                               f'The merged file already exists and was not overwritten:\n{exc.filename}')
        return
    except OSError as exc:
        messagebox.showerror('Could not save merged tally', str(exc))
        return

    key = f'{output.stem}_{merged.tally_num}'
    config_mod.tallies[key] = merged
    config_mod.output_files.append(output)
    settings_mod.readsave_legend()
    read_mod.refresh_tally_tree(treeview)
    treeview.change_state(key, 'checked')
    treeview.see(key)
    messagebox.showinfo('Tallies merged', f'Merged {len(selected)} tallies.\nSaved to:\n{output}')


def batch_merge_all_tallies(treeview):
    """Main-window batch action for the non-normalized source-sum merge mode."""
    try:
        output, completed, unmatched, skipped_merged, failures = batch_merge_tallies(
            config_mod.plot_settings['work_dir_path']
        )
    except OSError as exc:
        messagebox.showerror('Could not batch merge tallies', str(exc))
        return

    if not completed:
        details = []
        if unmatched:
            details.append(f'{unmatched} tally or tallies had no compatible partner.')
        if skipped_merged:
            details.append(f'{skipped_merged} previous merged result(s) were excluded.')
        if failures:
            details.extend(failures)
        messagebox.showwarning('No tallies merged', '\n'.join(details) or
                               'No compatible group of at least two tallies was found.')
        return

    merged_keys = []
    for entry in completed:
        merged = entry['merged']
        # Batch files tag even ordinary tally blocks as cell_1 so they reload
        # with a unique key beside cell/surface-item groups.
        item_suffix = f'_{entry["item"] or "cell_1"}'
        key = f'{output.stem}_{merged.tally_num}{item_suffix}'
        config_mod.tallies[key] = merged
        merged_keys.append(key)
    config_mod.output_files.append(output)
    settings_mod.readsave_legend()
    read_mod.refresh_tally_tree(treeview)
    for key in merged_keys:
        treeview.change_state(key, 'checked')
        treeview.see(key)

    message = f'Merged {len(completed)} compatible group(s).\nSaved file:\n{output}'
    if unmatched:
        message += f'\n\nSkipped {unmatched} tally or tallies without a compatible partner.'
    if skipped_merged:
        message += f'\nSkipped {skipped_merged} previously merged result(s).'
    if failures:
        message += '\n\nGroups not merged:\n' + '\n'.join(failures)
    messagebox.showinfo('Batch merge complete', message)
