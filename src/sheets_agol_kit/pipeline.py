"""Sync pipeline: raw responses -> clean tab.

The library provides the mechanics (read, iterate, write); the project
provides per-row logic via the build_row callback.
"""

from collections.abc import Callable
from typing import Any

import gspread

from .sheets import read_responses, write_rows


def sync(
    spreadsheet: gspread.Spreadsheet,
    *,
    responses_tab: str,
    output_tab: str,
    headers: list[str],
    build_row: Callable[[dict[str, Any]], list[Any] | None],
) -> tuple[int, int]:
    """Read the responses tab and rewrite the output tab.

    Args:
        spreadsheet: object from open_spreadsheet().
        responses_tab: tab where the Form stores responses (read-only).
        output_tab: clean tab that is fully rewritten.
        headers: output-tab headers.
        build_row: function(response_dict) -> list of values or None to
            skip that response (e.g. if geocoding failed).

    Returns (rows_written, total_responses).
    """
    responses = read_responses(spreadsheet, responses_tab)
    rows = [row for row in (build_row(r) for r in responses) if row is not None]
    write_rows(spreadsheet, output_tab, headers, rows)
    return len(rows), len(responses)
