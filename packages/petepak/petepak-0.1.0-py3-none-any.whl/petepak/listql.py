"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = petepak.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This file can be renamed depending on your needs or safely removed if not needed.

References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import logging
import sys
from collections.abc import Iterable
from collections import defaultdict
from typing import Callable, Any,Union
import csv

# from petepak import __version__

__author__ = "Peter Bernard"
__copyright__ = "Peter Bernard"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from petepak.skeleton import fib`,
# when using this Python module as a library.

import re

def expression_to_lambda(expr: str):
    """
    Converts expressions like:
      'a.id == b.id and a.age < b.age'
    into:
      lambda a, b: a.get('id') == b.get('id') and a.get('age') < b.get('age')
    """
    # Replace a.key → a.get('key'), b.key → b.get('key')
    expr = re.sub(r'\ba\.([a-zA-Z_][\w]*)', r"a.get('\1')", expr)
    expr = re.sub(r'\bb\.([a-zA-Z_][\w]*)', r"b.get('\1')", expr)

    # Validate allowed characters (basic safety)
    if not re.fullmatch(r"[a-zA-Z0-9_().'\" <>=!&|]+", expr):
        raise ValueError(f"Unsupported characters in expression: {expr}")
    if "===" in expr or "!==" in expr:
        raise ValueError(f"Invalid comparison operator in expression: {expr}")
    
    blacklist = ["exec", "eval", "import", "open", "__", "os.", "sys.", "subprocess"]
    if any(word in expr for word in blacklist):
        raise ValueError(f"Unsafe expression: contains forbidden keyword in '{expr}'")
    # Build and return the lambda
    return eval(f"lambda a, b: {expr}")

def inner_join(list1, list2, expr, list1_name='list1', list2_name='list2'):
    condition = expression_to_lambda(expr)
    all_keys_list1 = set().union(*(d.keys() for d in list1))
    all_keys_list2 = set().union(*(d.keys() for d in list2))

    result = []
    for a in list1:
        for b in list2:
            if condition(a, b):
                row = {
                    **{f"{list1_name}_{k}": a.get(k, None) for k in all_keys_list1},
                    **{f"{list2_name}_{k}": b.get(k, None) for k in all_keys_list2}
                }
                result.append(row)
    return result

def left_join(list1, list2, expr, list1_name='list1', list2_name='list2'):
    condition = expression_to_lambda(expr)
    all_keys_list1 = set().union(*(d.keys() for d in list1))
    all_keys_list2 = set().union(*(d.keys() for d in list2))

    result = []
    for a in list1:
        matches = [b for b in list2 if condition(a, b)]
        if matches:
            for b in matches:
                row = {
                    **{f"{list1_name}_{k}": a.get(k, None) for k in all_keys_list1},
                    **{f"{list2_name}_{k}": b.get(k, None) for k in all_keys_list2}
                }
                result.append(row)
        else:
            row = {
                **{f"{list1_name}_{k}": a.get(k, None) for k in all_keys_list1},
                **{f"{list2_name}_{k}": None for k in all_keys_list2}
            }
            result.append(row)
    return result
def right_join(list1, list2, expr, list1_name='list1', list2_name='list2'):
    condition = expression_to_lambda(expr)
    all_keys_list1 = set().union(*(d.keys() for d in list1))
    all_keys_list2 = set().union(*(d.keys() for d in list2))

    result = []
    for b in list2:
        matches = [a for a in list1 if condition(a, b)]
        if matches:
            for a in matches:
                row = {
                    **{f"{list1_name}_{k}": a.get(k, None) for k in all_keys_list1},
                    **{f"{list2_name}_{k}": b.get(k, None) for k in all_keys_list2}
                }
                result.append(row)
        else:
            row = {
                **{f"{list1_name}_{k}": None for k in all_keys_list1},
                **{f"{list2_name}_{k}": b.get(k, None) for k in all_keys_list2}
            }
            result.append(row)
    return result
def outer_join(list1, list2, expr, list1_name='list1', list2_name='list2'):
    condition = expression_to_lambda(expr)
    all_keys_list1 = set().union(*(d.keys() for d in list1))
    all_keys_list2 = set().union(*(d.keys() for d in list2))

    matched_pairs = set()
    result = []

    for a in list1:
        matched = False
        for b in list2:
            if condition(a, b):
                matched = True
                matched_pairs.add(id(b))
                row = {
                    **{f"{list1_name}_{k}": a.get(k, None) for k in all_keys_list1},
                    **{f"{list2_name}_{k}": b.get(k, None) for k in all_keys_list2}
                }
                result.append(row)
        if not matched:
            row = {
                **{f"{list1_name}_{k}": a.get(k, None) for k in all_keys_list1},
                **{f"{list2_name}_{k}": None for k in all_keys_list2}
            }
            result.append(row)

    for b in list2:
        if id(b) not in matched_pairs:
            row = {
                **{f"{list1_name}_{k}": None for k in all_keys_list1},
                **{f"{list2_name}_{k}": b.get(k, None) for k in all_keys_list2}
            }
            result.append(row)

    return result

def join(list1, list2, expr, join_type='inner', list1_name='list1', list2_name='list2'):
    """
    Dispatches to the appropriate join function based on join_type.

    Args:
        list1 (list[dict]): Left-side data.
        list2 (list[dict]): Right-side data.
        expr (str): Expression string like 'a.id == b.id'.
        join_type (str): One of 'inner', 'left', 'right', 'outer'.
        list1_name (str): Prefix for keys from list1.
        list2_name (str): Prefix for keys from list2.

    Returns:
        list[dict]: Joined result.
    """
    join_type = join_type.lower()
    if join_type == 'inner':
        return inner_join(list1, list2, expr, list1_name, list2_name)
    elif join_type == 'left':
        return left_join(list1, list2, expr, list1_name, list2_name)
    elif join_type == 'right':
        return right_join(list1, list2, expr, list1_name, list2_name)
    elif join_type == 'outer':
        return outer_join(list1, list2, expr, list1_name, list2_name)
    else:
        raise ValueError(f"Unsupported join_type: {join_type}")

def read_csv(file_path, separator=',', header=True, header_list=None, schema=None):
    """
    Reads a CSV file and returns a list of dictionaries, optionally casting values using a schema.

    Args:
        file_path (str): Path to the CSV file.
        separator (str): Field delimiter (default is comma).
        header (bool): Whether the file has a header row.
        header_list (list[str] | None): If header=False, provide column names manually.
        schema (dict[str, type] | None): Optional mapping of column names to types (e.g., {'id': int, 'score': float}).

    Returns:
        list[dict]: Parsed and optionally type-cast rows as dictionaries.
    """
    with open(file_path, newline='', encoding='utf-8') as f:
        if header:
            reader = csv.DictReader(f, delimiter=separator)
        else:
            if not header_list:
                raise ValueError("header_list must be provided when header=False")
            reader = csv.DictReader(f, delimiter=separator, fieldnames=header_list)

        rows = []
        for row in reader:
            if schema:
                casted = {}
                for key, value in row.items():
                    if key in schema:
                        try:
                            casted[key] = schema[key](value) if value != '' else None
                        except (ValueError, TypeError):
                            casted[key] = None
                    else:
                        casted[key] = value
                rows.append(casted)
            else:
                rows.append(row)

        return rows

def schema(rows):
    """
    Infers the schema of a list of dictionaries.

    Args:
        rows (list[dict]): Input data.

    Returns:
        dict: Mapping of keys to a list of observed value types.
    """
    type_map = {}

    for row in rows:
        for key, value in row.items():
            value_type = type(value).__name__
            type_map.setdefault(key, set()).add(value_type)

    # Convert sets to sorted lists for consistency
    return {key: sorted(types) for key, types in type_map.items()}

def write_csv(rows, file_path, separator=',', heading=True):
    """
    Writes a list of dictionaries to a CSV file.

    Args:
        rows (list[dict]): Data to write.
        file_path (str): Destination file path.
        separator (str): Field delimiter (default is comma).
        heading (bool): Whether to include a header row (default is True).
    """
    if not rows:
        raise ValueError("Cannot write empty data to CSV.")

    fieldnames = list(rows[0].keys())

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=separator)
        if heading:
            writer.writeheader()
        writer.writerows(rows)
        
def rename(
    rows: list[dict],
    old_or_mapping: Union[str, dict[str, str]],
    new_key: str = None
) -> list[dict]:
    """
    Renames one or more keys in each dictionary within a list.

    Args:
        rows (list[dict]): List of dictionaries to process.
        old_or_mapping (str | dict): Either a single old key name or a dict mapping old keys to new keys.
        new_key (str | None): If old_or_mapping is a string, this is the new key name.

    Returns:
        list[dict]: A new list with renamed keys.
    """
    if isinstance(old_or_mapping, str):
        mapping = {old_or_mapping: new_key}
    else:
        mapping = old_or_mapping

    result = []
    for row in rows:
        new_row = row.copy()
        for old_key, new_key in mapping.items():
            new_row[new_key] = new_row.pop(old_key) if old_key in new_row else None
        result.append(new_row)

    return result



def transform(
    rows: list[dict],
    column_or_mapping: Union[str, dict[str, Callable[[dict], Any]]],
    transformation: Callable[[dict], Any] = None
) -> list[dict]:
    """
    Applies one or more transformation functions to a list of dictionaries.

    Args:
        rows (list[dict]): Input data.
        column_or_mapping (str | dict): Either a single column name or a dict mapping column names to functions.
        transformation (Callable | None): If column_or_mapping is a string, this is the function to apply.

    Returns:
        list[dict]: A new list with transformed columns.
    """
    result = []

    if isinstance(column_or_mapping, str):
        transformations = {column_or_mapping: transformation}
    else:
        transformations = column_or_mapping

    for row in rows:
        new_row = row.copy()
        for col, func in transformations.items():
            try:
                new_row[col] = func(new_row)
            except Exception:
                new_row[col] = None
        result.append(new_row)

    return result



def select(rows: list[dict], columns: list[str]) -> list[dict]:
    """
    Selects a subset of columns from each dictionary in a list.

    Args:
        rows (list[dict]): Input data.
        columns (list[str]): List of column names to extract.

    Returns:
        list[dict]: A new list containing only the selected columns.

    Raises:
        KeyError: If any column is missing from a row.
    """
    result = []
    for i, row in enumerate(rows):
        try:
            selected = {col: row[col] for col in columns}
        except KeyError as e:
            raise KeyError(f"Missing column '{e.args[0]}' in row {i}: {row}") from None
        result.append(selected)
    return result
  

def filter(rows: list[dict], predicate: Union[str, Callable[[dict], bool]]) -> list[dict]:
    """
    Filters a list of dictionaries using either an expression string or a predicate function.

    Args:
        rows (list[dict]): Input data.
        predicate (str | Callable): Either an expression string using 'a' as the row variable,
                                  or a function that takes a row and returns True to keep it.

    Returns:
        list[dict]: A new list containing only rows that satisfy the predicate.

    Examples:
        # Using expression string
        filter(data, "a.score >= 80")
        
        # Using lambda function
        filter(data, lambda row: row.get('score', 0) >= 80)
    """
    if isinstance(predicate, str):
        # Convert expression string to lambda
        expr_lambda = expression_to_lambda(predicate)
        return [row.copy() for row in rows if expr_lambda(row, None)]
    else:
        # Use the predicate function directly
        return [row.copy() for row in rows if predicate(row)]

def group_by(rows: list[dict], keys: Union[str, list[str]]) -> list[list[dict]]:
    """
    Groups a list of dictionaries by one or more key values.

    Args:
        rows (list[dict]): Input data.
        keys (Union[str, list[str]]): A single key or list of keys to group by.

    Returns:
        list[list[dict]]: A list of groups, where each group is a list of dictionaries
                          sharing the same values for the specified key(s).

    Raises:
        KeyError: If any key is missing in a row.
    """
    if isinstance(keys, str):
        keys = [keys]

    groups = defaultdict(list)
    for i, row in enumerate(rows):
        try:
            group_key = tuple(row[k] for k in keys)
        except KeyError as e:
            raise KeyError(f"Missing key '{e.args[0]}' in row {i}: {row}") from None
        groups[group_key].append(row.copy())
    return list(groups.values())

def display(rows: list[dict]) -> None:
    """
    Prints a list of dictionaries as a formatted table.

    Args:
        rows (list[dict]): Input data to display.
    """
    if not rows:
        print("(no data)")
        return

    # Collect all unique keys across rows
    columns = sorted({key for row in rows for key in row.keys()})
    
    # Compute column widths
    col_widths = {col: max(len(str(col)), max(len(str(row.get(col, ''))) for row in rows)) for col in columns}

    # Print header
    header = " | ".join(f"{col:<{col_widths[col]}}" for col in columns)
    divider = "-+-".join("-" * col_widths[col] for col in columns)
    print(header)
    print(divider)

    # Print rows
    for row in rows:
        line = " | ".join(f"{str(row.get(col, '')):<{col_widths[col]}}" for col in columns)
        print(line)

def order_by(
    rows: list[dict],
    keys: Union[str, list[str], Callable[[dict], Any]],
    reverse: bool = False
) -> list[dict]:
    if callable(keys):
        key_func = keys
    elif isinstance(keys, str):
        key_func = lambda row: row.get(keys, float('-inf'))
    elif isinstance(keys, list):
        key_func = lambda row: tuple(row.get(k, float('-inf')) for k in keys)
    else:
        raise TypeError("keys must be a string, list of strings, or a callable")

    return sorted(rows, key=key_func, reverse=reverse)

def distinct(rows: list[dict], keys: Union[str, list[str]]) -> list[dict]:
    """
    Returns a list of unique rows based on one or more key values.

    Args:
        rows (list[dict]): Input data.
        keys (str | list[str]): Key or keys to determine uniqueness.

    Returns:
        list[dict]: Deduplicated list of rows.
    """
    if isinstance(keys, str):
        keys = [keys]

    seen = set()
    result = []

    for row in rows:
        try:
            key_tuple = tuple(row[k] for k in keys)
        except KeyError as e:
            raise KeyError(f"Missing key '{e.args[0]}' in row: {row}") from None

        if key_tuple not in seen:
            seen.add(key_tuple)
            result.append(row.copy())

    return result


def display_grouped(groups: list[list[dict]], group_keys: Union[str, list[str]]) -> None:
    """
    Displays grouped data as formatted tables with group headings.

    Args:
        groups (list[list[dict]]): Grouped data (output of group_by).
        group_keys (str | list[str]): Key(s) used for grouping.
    """
    if isinstance(group_keys, str):
        group_keys = [group_keys]

    for i, group in enumerate(groups):
        if not group:
            continue

        # Group header
        label = ", ".join(f"{k}={group[0].get(k)}" for k in group_keys)
        print(f"\nGroup {i+1}: {label}")

        # Collect all unique keys across rows
        columns = sorted({key for row in group for key in row})
        col_widths = {col: max(len(str(col)), max(len(str(row.get(col, ''))) for row in group)) for col in columns}

        # Print header
        header = " | ".join(f"{col:<{col_widths[col]}}" for col in columns)
        divider = "-+-".join("-" * col_widths[col] for col in columns)
        print(header)
        print(divider)

        # Print rows
        for row in group:
            line = " | ".join(f"{str(row.get(col, '')):<{col_widths[col]}}" for col in columns)
            print(line)


