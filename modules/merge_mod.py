"""Sum source contributions or pool histories using MCNP tally statistics.

See doc/tally_merge.md for the manual references, formulas, and assumptions.
"""

from datetime import datetime
import math
from pathlib import Path
from tkinter import messagebox

from modules import config_mod, read_mod, settings_mod
from modules.tally_data import Tally


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
    lines = [
        'MCNP TallyPlotter merged tally output (postprocessed)\n',
        description,
        error_description,
        'Original MCNP statistical checks are not applicable to this merged tally.\n',
        'particle energy cutoffs                                     print table 101\n',
        '\n', '\n', '\n', '\n', '\n',
        f' 1 0 {merged.particle.removesuffix("s")} {merged.cutoff_energy:.17e}\n',
        '\n',
        f'1tally {merged.tally_num}       nps = {merged.nps}\n',
        '+ ' + merged.comment.replace('\n', ' ').replace('\r', ' ') + '\n',
        f' tally type {merged.tally_type}\n',
        f' particle(s): {merged.particle}\n',
        ' cell 1\n',
        ' energy         tally         relative error\n',
    ]
    for energy, value, error in zip(merged.energy[1:], merged.flux[1:], merged.error[1:]):
        lines.append(f' {energy:.17e} {value:.17e} {error:.17e}\n')
    lines.extend([f' total {merged.total:.17e} {merged.total_error:.17e}\n',
                  '\n', ' end of merged tally\n'])
    suffix = '_NPSnorm' if normalize_by_nps else ''
    output = Path(directory) / f'merged_{datetime.now():%Y%m%d_%H%M%S_%f}{suffix}.o'
    # Exclusive creation avoids overwriting an existing result even on a timestamp collision.
    with output.open('x', encoding='utf-8') as stream:
        try:
            stream.writelines(lines)
            stream.flush()
        except OSError:
            stream.close()
            output.unlink()
            raise
    return output, merged


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
