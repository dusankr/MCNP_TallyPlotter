"""Sorting helpers shared by the main tally tree view."""


NUMERIC_COLUMNS = frozenset({
    'Tally number',
    'Tally type',
    'NPS',
    'Number of values',
    'E_cut-off (MeV)',
    'E_min (MeV)',
    'E_max (MeV)',
    'Rel. Error',
    'VoV',
    'Slope',
    'FoM',
})


def _number_or_none(value):
    """Convert displayed numeric values, including scientific notation, when possible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sort_treeview_column(tree, column, reverse):
    """Sort one tree column, preserving checkbox state and alternating row colors."""
    data = [(tree.set(child, column), child) for child in tree.get_children('')]

    if column in NUMERIC_COLUMNS:
        numeric = [(number, value, child) for value, child in data
                   if (number := _number_or_none(value)) is not None]
        non_numeric = [(str(value).casefold(), child) for value, child in data
                       if _number_or_none(value) is None]
        numeric.sort(key=lambda item: item[0], reverse=reverse)
        # Values such as N/A remain after real numbers in both sort directions.
        non_numeric.sort(key=lambda item: item[0], reverse=reverse)
        ordered = [(value, child) for _, value, child in numeric]
        ordered.extend((value, child) for value, child in non_numeric)
    else:
        ordered = sorted(data, key=lambda item: str(item[0]).casefold(), reverse=reverse)

    for index, (_, child) in enumerate(ordered):
        tree.move(child, '', index)

    for index, (_, child) in enumerate(ordered):
        row_tag = 'oddrow' if index % 2 == 0 else 'evenrow'
        current_tags = tree.item(child, 'tags')
        checkbox_state = [tag for tag in current_tags if tag in ('checked', 'unchecked')]
        status_tags = [tag for tag in current_tags if tag == 'zero_values']
        tree.item(child, tags=tuple(status_tags) + tuple(checkbox_state) + (row_tag,))

    tree.heading(column, command=lambda: sort_treeview_column(tree, column, not reverse))
