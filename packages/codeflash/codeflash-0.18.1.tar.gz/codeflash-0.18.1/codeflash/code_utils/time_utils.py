from __future__ import annotations

import datetime as dt
import re

import humanize


def humanize_runtime(time_in_ns: int) -> str:
    runtime_human: str = str(time_in_ns)
    units = "nanoseconds"
    if 1 <= time_in_ns < 2:
        units = "nanosecond"

    if time_in_ns / 1000 >= 1:
        time_micro = float(time_in_ns) / 1000
        runtime_human = humanize.precisedelta(dt.timedelta(microseconds=time_micro), minimum_unit="microseconds")

        units = re.split(r",|\s", runtime_human)[1]

        if units in {"microseconds", "microsecond"}:
            runtime_human = f"{time_micro:.3g}"
        elif units in {"milliseconds", "millisecond"}:
            runtime_human = "%.3g" % (time_micro / 1000)
        elif units in {"seconds", "second"}:
            runtime_human = "%.3g" % (time_micro / (1000**2))
        elif units in {"minutes", "minute"}:
            runtime_human = "%.3g" % (time_micro / (60 * 1000**2))
        elif units in {"hour", "hours"}:  # hours
            runtime_human = "%.3g" % (time_micro / (3600 * 1000**2))
        else:  # days
            runtime_human = "%.3g" % (time_micro / (24 * 3600 * 1000**2))
    runtime_human_parts = str(runtime_human).split(".")
    if len(runtime_human_parts[0]) == 1:
        if runtime_human_parts[0] == "1" and len(runtime_human_parts) > 1:
            units = units + "s"
        if len(runtime_human_parts) == 1:
            runtime_human = f"{runtime_human_parts[0]}.00"
        elif len(runtime_human_parts[1]) >= 2:
            runtime_human = f"{runtime_human_parts[0]}.{runtime_human_parts[1][0:2]}"
        else:
            runtime_human = (
                f"{runtime_human_parts[0]}.{runtime_human_parts[1]}{'0' * (2 - len(runtime_human_parts[1]))}"
            )
    elif len(runtime_human_parts[0]) == 2:
        if len(runtime_human_parts) > 1:
            runtime_human = f"{runtime_human_parts[0]}.{runtime_human_parts[1][0]}"
        else:
            runtime_human = f"{runtime_human_parts[0]}.0"
    else:
        runtime_human = runtime_human_parts[0]

    return f"{runtime_human} {units}"


def format_time(nanoseconds: int) -> str:
    """Format nanoseconds into a human-readable string with 3 significant digits when needed."""
    # Define conversion factors and units
    if not isinstance(nanoseconds, int):
        raise TypeError("Input must be an integer.")
    if nanoseconds < 0:
        raise ValueError("Input must be a positive integer.")

    if nanoseconds < 1_000:
        return f"{nanoseconds}ns"
    if nanoseconds < 1_000_000:
        value = nanoseconds / 1_000
        return f"{value:.2f}μs" if value < 10 else (f"{value:.1f}μs" if value < 100 else f"{int(value)}μs")
    if nanoseconds < 1_000_000_000:
        value = nanoseconds / 1_000_000
        return f"{value:.2f}ms" if value < 10 else (f"{value:.1f}ms" if value < 100 else f"{int(value)}ms")
    value = nanoseconds / 1_000_000_000
    return f"{value:.2f}s" if value < 10 else (f"{value:.1f}s" if value < 100 else f"{int(value)}s")


def format_perf(percentage: float) -> str:
    """Format percentage into a human-readable string with 3 significant digits when needed."""
    # Branch order optimized
    abs_perc = abs(percentage)
    if abs_perc >= 100:
        return f"{percentage:.0f}"
    if abs_perc >= 10:
        return f"{percentage:.1f}"
    if abs_perc >= 1:
        return f"{percentage:.2f}"
    return f"{percentage:.3f}"
