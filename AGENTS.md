# AGENTS.md

## Project Overview

This project is a desktop application written in Python using Tkinter and ttk.

The primary goals are:
- Maintainable, modular, and readable code.
- Reliable operation and long-term compatibility.
- Clear separation between GUI and application logic.
- Efficient development without unnecessary complexity.

## Technology Stack

- Language: Python 3.12+
- GUI: Tkinter, ttk, and the existing ttkwidgets components
- Plotting: Matplotlib embedded with FigureCanvasTkAgg and NavigationToolbar2Tk
- Numerical processing: NumPy and SciPy, when needed
- Configuration: TOML using tomllib and tomli_w
- Input files: MCNP output files; additional formats require their own readers
- Testing: the existing standard-library unittest suite
- Dependency management: Follow the existing project configuration.

Do not introduce additional frameworks or dependencies without explaining why they are necessary.

## Architecture

- Separate GUI code from business logic and data processing.
- Use one `tk.Tk` root and owned `tk.Toplevel` windows.
- Use reusable ttk frames for major interface components.
- Construct interfaces programmatically using grid or pack layout managers.
- Keep individual classes and modules focused on a clear responsibility.
- Avoid circular imports and unnecessary global state.
- Do not overengineer simple functionality.

Preserve the current directory structure while improving boundaries incrementally:

```text
MCNP_TallyPlotter/
├── AGENTS.md
├── mcnp_tally_plot_main.py
├── modules/
├── tests/
└── doc/
```

Adapt this structure to actual project requirements.

## Coding Conventions

- Follow PEP 8.
- Use descriptive names for variables, functions, and classes.
- Use type hints for public functions and methods.
- Prefer standard Python libraries where practical.
- Use `pathlib` for filesystem operations.
- Use Python logging instead of print statements for diagnostics.
- Write docstrings for public classes and nontrivial functions.
- Avoid unnecessary comments explaining obvious code.
- Prefer straightforward implementations over clever abstractions.
- Preserve existing conventions unless there is a good reason to change them.

## Tkinter Guidelines

- Prefer standard ttk widgets and existing ttkwidgets components.
- Use layout managers instead of absolute positioning; do not mix grid and pack within the same parent.
- Keep computational logic outside GUI classes.
- Use explicit callbacks and carefully managed variable traces for communication.
- Suppress traces during configuration synchronization to avoid recursive saves and redraws.
- Give dialogs an explicit parent; make child editors transient to their owning window.
- Use grabs only for modal interactions and restore the previous grab on every close path.
- Handle WM_DELETE_WINDOW as well as close buttons; avoid permanent topmost windows.
- Never perform long-running calculations in the GUI thread.
- Use worker threads/processes for lengthy work and queues polled with after() for GUI updates.
- Update GUI widgets only from the main GUI thread.
- Ensure proper cleanup of workers, threads, and external resources.
- Use ttk.Treeview for tabular data and keep the underlying dataset independent of widgets.
- Keep Matplotlib rendering separate from Tk canvas ownership and numerical transformations.
- Avoid excessive custom styling when standard ttk widgets are sufficient.

## Error Handling

- Handle expected errors explicitly.
- Do not silently suppress exceptions.
- Provide understandable error messages to users.
- Log technical details useful for debugging.
- Avoid broad `except Exception` blocks unless handling an application boundary.
- Do not hide failures by returning fabricated or placeholder results.

## Testing

- Use unittest for automated testing: `venv\Scripts\python.exe -m unittest discover -s tests -v`.
- Keep core functionality independently testable without launching the GUI.
- Add or update tests when changing important functionality.
- Include tests for edge cases and invalid inputs.
- Do not modify tests merely to make failing code appear correct.
- Report tests that could not be executed.

## Working with the Existing Codebase

Before making changes:

1. Inspect relevant files and understand the existing implementation.
2. Reuse existing functions and components where appropriate.
3. Identify potential impacts on other modules.
4. Prefer targeted modifications over unnecessary rewrites.

When implementing changes:

1. Keep changes focused on the requested task.
2. Preserve existing functionality unless a change is explicitly requested.
3. Update affected imports, tests, and documentation.
4. Avoid unrelated refactoring.
5. Do not delete existing functionality without explaining the reason.

## Agent Workflow

- For complex tasks, briefly outline the proposed implementation before making substantial changes.
- For straightforward tasks, implement directly.
- Make reasonable implementation decisions without asking about every minor detail.
- Ask for clarification when requirements are genuinely ambiguous or a decision would significantly affect architecture.
- Do not claim that code has been tested unless tests were actually executed.
- After making changes, summarize:
  - What changed.
  - Which files were modified.
  - What tests or checks were performed.
  - Any remaining limitations or known issues.

## Git and File Safety

- Do not overwrite or discard unrelated user changes.
- Do not run destructive Git commands without explicit approval.
- Do not commit or push changes unless requested.
- Do not modify dependency lockfiles unnecessarily.
- Do not add generated files, caches, or temporary artifacts to version control.
- Never hardcode passwords, API keys, or other secrets.

## Documentation

- Keep README.md updated when installation or usage changes.
- Document non-obvious design decisions.
- Update relevant documentation when public APIs or configuration change.
- Avoid excessive documentation for trivial implementation details.
