# MCNP Plotter: staged improvement plan

## Approach

Deliver the small plotting improvements first, followed by architecture work and parser expansion. Each step should be independently reviewable and usable.

Phase 1 was implemented and committed as `ca60553`. The plotting-control follow-up below is also implemented. Larger integrations still include explicit review checkpoints using your example files and independent code.

## Phase 1 — Small fixes and plotting features

**Status: Steps 1–3 completed.** The original requirements below are retained as the milestone record; the follow-up replaces the initial average checkbox. The original two-tab layout is retained.

### Step 1: Tkinter guidance, figure saving, and ratio titles

- Adapt `AGENTS.md` from PySide6 to Tkinter/ttk: one `Tk` root, owned `Toplevel` windows, layout managers, explicit dialog parents, controlled grabs, and main-thread-only widget updates.
- Specify Matplotlib’s Tk canvas, TOML configuration, and the existing `unittest` suite. Keep the current project layout; do not require an immediate directory migration.
- Remove the successful-picture-save confirmation. Retain the filename dialog, overwrite protection, and actionable error dialogs.
- Parent save dialogs to the plot window. Review editor ownership and grab restoration on both button-close and window-close paths. Avoid permanent “always on top” settings.
- Treat save cancellation as normal. Restore figure dimensions and clear save state on success, cancellation, and failure.
- Default the ratio Y title to **`Ratio (-)`**, with the existing separate custom ratio title taking precedence. Restore the ordinary Y title when ratio mode ends.

### Step 2: Independent axis-title presets

- Add an **Axis titles** frame with independent X, Y, and secondary-Y controls supporting **Auto**, named presets, and **Custom**.
- Store named presets in `axis_titles.toml`, using named entries with a label value and description, similar to multiplier presets.
- Start with the existing automatic labels as examples. Title presets change labels only.
- During ratio mode, the primary Y control edits the separate ratio title; ordinary Y settings remain preserved.
- Support editing the preset file through the existing editor and reloading external edits through **Reload settings**.
- Preserve existing configuration compatibility. Missing new settings use defaults; invalid preset files retain the last valid presets and report the problem.

### Step 3: Moving-average overlay

- Add a **Moving average** frame with an enable checkbox and odd-number bin-window control. Default: disabled, window size **5**.
- Calculate a centered, equal-weight arithmetic average of adjacent real bins. Use shorter windows at dataset boundaries; exclude the artificial cutoff placeholder.
- Apply it after normalization/multiplier processing, or after ratio calculation in ratio mode. Changing axis limits must not change the computed average.
- Draw a distinguishable overlay in the original curve’s color, with a legend suffix showing its window size. Position values at bin centers.
- Keep original curves and their error bars. Do not assign uncertainty estimates to the overlay.
- Treat zero-denominator ratio bins and nonfinite values as gaps in the overlay; do not smooth across those gaps.
- Persist controls through configuration reload and restart. Include overlays in saved figures; leave source data, merges, and numerical exports unchanged.

### Completed follow-up: display modes and F8 cleanup

- Replaced the average checkbox with **Original only**, **Original + average**, and **Average only**. Average only hides original curves and error bars, preserves the error-bar preference, and uses the normal line styles. Averaging, ratio gaps, and saved figures retain their existing behavior.
- Added `plot.moving_average_mode` (`original`, `both`, `average`). Legacy booleans migrate to `original`/`both`; explicit new modes take precedence and saves write only the new key.
- The four-tab reorganization was reversed at the user's request. The current tabs are **Plot settings** and **Average**. Plot settings retains two columns, with **Axis and plot titles** in its scrollable second column; Average contains the curve-display controls. Replot/quit controls remain below both tabs.
- Removed the disabled F8-specific first-two-row skipping blocks. Imports retain all reported rows; the general first-bin visibility control remains available.
- Regression coverage includes display modes, legacy configuration, restored preferences, the restored two-tab layout, and F8 row retention for single and multiple cells.

## Phase 2 — Frontend/backend boundaries and activity reporting

### Step 4: Establish boundaries incrementally

Keep the desktop application in one process; no web frontend or server is needed.

- **Frontend:** Tkinter widgets, dialogs, selection, user commands, and embedded plot windows.
- **Application layer:** coordinates loading, saving, plotting, merging, settings, and progress reporting.
- **Backend:** parsing, numerical transformations, validation, and merge calculations; receives explicit inputs and returns results without accessing widgets.
- **Rendering:** receives prepared curves and settings and draws into supplied Matplotlib axes. Tk canvas ownership stays in the frontend.
- Introduce an application-state object and per-window plot state to gradually replace shared globals. Preserve compatibility adapters while migrating existing callers.
- Establish a parser result containing datasets and diagnostics. Store source path, tally number, and cell/surface identity explicitly rather than recovering them from display strings.
- Add a guarded application entry point so importing modules does not launch the GUI.

### Step 5: Add the activity panel

- Add a collapsible, scrollable, read-only activity panel in the main window, with Clear and Copy controls.
- Replace application `print` diagnostics with Python logging: timestamps, severity, and useful file/tally context.
- Route logs through a queue drained by Tk’s `after()` callback. Bound retained output to prevent unlimited growth.
- Report loading summaries, skipped tallies, parse failures, merges, config reloads, and saves.
- Move lengthy loading operations to a worker through the application layer. Apply results to widgets on the main thread and clean up workers/resources on shutdown.
- Keep actionable error dialogs where appropriate; routine progress and success messages belong in the panel.

## Phase 3 — Parser reliability and format expansion

### Step 6: Output parser review and supported-tally expansion

**TODO — Investigate proper F8 plotting:** use representative F8 outputs and the MCNP manual to establish how special initial bins, energy normalization, and logarithmic axes should be handled. Preserve every reported row while investigating; do not reintroduce automatic first-bin skipping. This requires a separate, reviewed plotting decision after examining real examples.

**Input checkpoint:** review your real multi-cell output example before changing parsing behavior.

- Compare the example with the existing synthetic multi-cell tests and the supplied MCNP manual.
- Replace fixed line offsets with explicit tally/block boundaries and controlled parser states.
- Preserve each independent cell/surface dataset, its values, errors, totals, NPS, and identity. Prevent metadata leaking between blocks.
- Preserve existing merged-output reload compatibility and ordinary plotting behavior.
- Add unsupported energy-binned tally layouts incrementally, using representative fixtures.
- Explicitly exclude **F6, single-value tallies, and special radiography tallies**, as agreed. Report unsupported layouts without misinterpreting them as ordinary spectra.

### Step 7: MCTAL integration

**Design checkpoint:** inspect representative MCTAL files and corresponding output files, then agree on the supported dimensions and tally variants.

- Implement a separate reader behind the common parser-result interface.
- Initially target energy-binned datasets already supported by the output reader.
- Preserve cell/surface identity and other dimensions explicitly; never silently flatten multidimensional data.
- Compare values, uncertainties, bin boundaries, totals, and NPS against equivalent output-file results.
- Integrate loading, table display, plotting, and applicable merge validation through the shared application layer.
- Require a reviewed format/support specification before starting the parser implementation.

### Step 8: Fmesh integration

**Design checkpoint:** review your independent implementation, a representative XDMF file, and its referenced HDF5 runtape.

- Separate mesh loading and numerical operations from its plotting controls.
- Introduce a dedicated mesh dataset model rather than forcing mesh arrays into the current spectrum model.
- Resolve referenced files relative to the XDMF location where applicable; validate dataset paths, dimensions, and geometry.
- Load requested data slices where the file layout permits, avoiding unnecessary full-runtape reads.
- Integrate a dedicated mesh plot window using the shared settings, activity reporting, and save-dialog conventions.
- Agree on initial geometry, slicing, energy selection, and color-scale controls after reviewing the supplied code. Document this contract before implementation.

MCTAL and fmesh can proceed independently once the shared boundaries are established.

## Validation and delivery

- **Small fixes:** manually verify Windows dialog stacking, editor closure, save cancellation/failure, and ratio-title restoration.
- **Presets/settings:** verify internal-editor saves, external-file reloads, invalid TOML handling, and restart persistence.
- **Moving average:** verify known numerical results, boundaries, short datasets, zeros, invalid ratio bins, redraws, and unchanged source data.
- **Architecture/activity:** verify backend use without launching Tk, responsive loading, main-thread widget updates, and clean shutdown.
- **Parsers:** use real fixtures plus regression tests for multiple cells, spacing variations, malformed/truncated blocks, excluded types, and merged-file round trips.
- **New formats:** compare imported data against independently known results before enabling broader support.

Steps 1–3 and the plotting-control follow-up are complete. The larger restructuring remains in Phase 2, followed by the example-driven parser and format work in Phase 3.
