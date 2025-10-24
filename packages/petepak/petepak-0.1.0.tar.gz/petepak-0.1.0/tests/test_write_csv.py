import pytest
import tempfile
import os
import csv
from petepak.listql import write_csv  # Adjust import path as needed

def read_csv_raw(path, separator=','):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.reader(f, delimiter=separator))

def create_temp_path():
    """Create a temp file path and release the file descriptor to avoid locking issues."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    return path

def test_write_csv_basic():
    data = [
        {'id': 1, 'name': 'Alice', 'score': 95.5},
        {'id': 2, 'name': 'Bob', 'score': 88.0}
    ]
    path = create_temp_path()
    try:
        write_csv(data, path)
        rows = read_csv_raw(path)
        assert rows == [
            ['id', 'name', 'score'],
            ['1', 'Alice', '95.5'],
            ['2', 'Bob', '88.0']
        ]
    finally:
        os.remove(path)

def test_write_csv_custom_separator():
    data = [
        {'id': 1, 'name': 'Alice'},
        {'id': 2, 'name': 'Bob'}
    ]
    path = create_temp_path()
    try:
        write_csv(data, path, separator='|')
        rows = read_csv_raw(path, separator='|')
        assert rows == [
            ['id', 'name'],
            ['1', 'Alice'],
            ['2', 'Bob']
        ]
    finally:
        os.remove(path)

def test_write_csv_empty_data_raises():
    path = create_temp_path()
    try:
        with pytest.raises(ValueError):
            write_csv([], path)
    finally:
        os.remove(path)

def test_write_csv_preserves_column_order():
    data = [
        {'name': 'Alice', 'id': 1},
        {'name': 'Bob', 'id': 2}
    ]
    path = create_temp_path()
    try:
        write_csv(data, path)
        rows = read_csv_raw(path)
        assert rows[0] == ['name', 'id']  # order from first dict
    finally:
        os.remove(path)
def test_write_csv_without_heading():
    data = [
        {'id': 1, 'name': 'Alice'},
        {'id': 2, 'name': 'Bob'}
    ]
    path = create_temp_path()
    try:
        write_csv(data, path, heading=False)
        rows = read_csv_raw(path)
        assert rows == [
            ['1', 'Alice'],
            ['2', 'Bob']
        ]
    finally:
        os.remove(path)

def test_write_csv_without_heading_custom_separator():
    data = [
        {'id': 1, 'name': 'Alice'},
        {'id': 2, 'name': 'Bob'}
    ]
    path = create_temp_path()
    try:
        write_csv(data, path, separator='|', heading=False)
        rows = read_csv_raw(path, separator='|')
        assert rows == [
            ['1', 'Alice'],
            ['2', 'Bob']
        ]
    finally:
        os.remove(path)