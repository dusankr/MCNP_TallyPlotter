"""Numerical moving averages without changing source tally data."""

import math


def validate_window(value) -> int:
    """Require an odd, positive number of bins."""
    if isinstance(value, bool):
        raise ValueError('The moving-average window must be a positive odd integer.')
    try:
        number = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError('The moving-average window must be a positive odd integer.') from exc
    if not math.isfinite(number) or not number.is_integer() or number < 1 or int(number) % 2 == 0:
        raise ValueError('The moving-average window must be a positive odd integer.')
    return int(number)


def centered_moving_average(values, window: int) -> list[float]:
    """Average finite contiguous runs, shortening windows at edges and gaps."""
    window = validate_window(window)
    data = list(values)
    result = [math.nan] * len(data)
    radius = window // 2
    start = 0
    while start < len(data):
        if not math.isfinite(data[start]):
            start += 1
            continue
        end = start
        while end < len(data) and math.isfinite(data[end]):
            end += 1
        for index in range(start, end):
            left = max(start, index - radius)
            right = min(end, index + radius + 1)
            # Divide before summing to avoid overflowing for large finite scores.
            result[index] = math.fsum(value / (right - left) for value in data[left:right])
        start = end
    return result
