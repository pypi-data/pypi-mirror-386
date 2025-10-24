from typing import List, Tuple, Union

import click
from tabulate import tabulate


@click.command()
@click.argument('file_before', type=click.Path(exists=True))
@click.argument('file_after', type=click.Path(exists=True))
def subsets(file_before, file_after):
    """
    Compare two subset files and display changes in test order positions
    """

    # Read files and map test paths to their indices
    with open(file_before, 'r') as f:
        before_tests = f.read().splitlines()
    before_index_map = {test: idx for idx, test in enumerate(before_tests)}

    with open(file_after, 'r') as f:
        after_tests = f.read().splitlines()
    after_index_map = {test: idx for idx, test in enumerate(after_tests)}

    # List of tuples representing test order changes (before, after, diff, test)
    rows: List[Tuple[Union[int, str], Union[int, str], Union[int, str], str]] = []

    # Calculate order difference and add each test in file_after to changes
    for after_idx, test in enumerate(after_tests):
        if test in before_index_map:
            before_idx = before_index_map[test]
            diff = after_idx - before_idx
            rows.append((before_idx + 1, after_idx + 1, diff, test))
        else:
            rows.append(('-', after_idx + 1, 'NEW', test))

    # Add all deleted tests to changes
    for before_idx, test in enumerate(before_tests):
        if test not in after_index_map:
            rows.append((before_idx + 1, '-', 'DELETED', test))

    # Sort changes by the order diff
    rows.sort(key=lambda x: (0 if isinstance(x[2], str) else 1, x[2]))

    # Display results in a tabular format
    headers = ["Before", "After", "After - Before", "Test"]
    tabular_data = [
        (before, after, f"{diff:+}" if isinstance(diff, int) else diff, test)
        for before, after, diff, test in rows
    ]
    click.echo_via_pager(tabulate(tabular_data, headers=headers, tablefmt="github"))
