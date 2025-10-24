import pytest
from petepak.listql import rename  # Adjust import path if needed

def test_rename_single_key():
    data = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
    result = rename(data, 'name', 'username')
    assert result == [
        {'id': 1, 'username': 'Alice'},
        {'id': 2, 'username': 'Bob'}
    ]
    assert data == [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]  # original unchanged

def test_rename_single_key_missing():
    data = [{'id': 1}, {'id': 2, 'name': 'Bob'}]
    result = rename(data, 'name', 'username')
    assert result == [
        {'id': 1, 'username': None},
        {'id': 2, 'username': 'Bob'}
    ]

def test_rename_many_keys():
    data = [{'id': 1, 'name': 'Alice', 'score': 90}]
    result = rename(data, {'name': 'username', 'score': 'points'})
    assert result == [{'id': 1, 'username': 'Alice', 'points': 90}]

def test_rename_many_keys_with_missing():
    data = [{'id': 1}, {'id': 2, 'score': 75}]
    result = rename(data, {'name': 'username', 'score': 'points'})
    assert result == [
        {'id': 1, 'username': None, 'points': None},
        {'id': 2, 'username': None, 'points': 75}
    ]

def test_rename_empty_input():
    result = rename([], 'name', 'username')
    assert result == []

def test_rename_preserves_original_rows():
    data = [{'a': 1, 'b': 2}]
    result = rename(data, 'b', 'c')
    assert data == [{'a': 1, 'b': 2}]
    assert result == [{'a': 1, 'c': 2}]

