"""
Petepak - A Python package for SQL-like data manipulation on lists of dictionaries.

Petepak provides a comprehensive set of functions for data manipulation that mimics
SQL operations but works directly on Python lists of dictionaries. It includes:

- SQL-like operations: select, filter, join, group_by, order_by
- Multiple join types: inner, left, right, outer joins  
- CSV I/O: read_csv, write_csv with schema support
- Data transformation: rename, transform, distinct
- Sorting algorithms: bubble, merge, quick sort
- Expression evaluation: Safe string-to-lambda conversion

Example:
    >>> from petepak import select, filter, join
    >>> data = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
    >>> filtered = filter(data, "a.id > 1")
    >>> result = select(filtered, ['name'])
"""

__version__ = "0.1.0"
__author__ = "Peter Bernard"
__email__ = "peter.a.bernard1@gmail.com"

from .listql import (
    select, filter, join, group_by, order_by, distinct, transform, rename,
    read_csv, write_csv, schema, display, display_grouped
)
from .sorting import bubble_sort, merge_sort, quick_sort

__all__ = [
    # Core data manipulation
    'select', 'filter', 'join', 'group_by', 'order_by', 'distinct', 
    'transform', 'rename',
    # I/O operations
    'read_csv', 'write_csv', 'schema',
    # Display functions
    'display', 'display_grouped',
    # Sorting algorithms
    'bubble_sort', 'merge_sort', 'quick_sort'
]


