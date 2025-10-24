import pytest
from petepak.listql import distinct  # Adjust import path if needed

def test_distinct_single_key():
    data = [
        {'id': 1, 'name': 'Alice'},
        {'id': 2, 'name': 'Bob'},
        {'id': 1, 'name': 'Alice'},  # duplicate id
    ]
    result = distinct(data, 'id')
    assert result == [
        {'id': 1, 'name': 'Alice'},
        {'id': 2, 'name': 'Bob'}
    ]

def test_distinct_multiple_keys():
    data = [
        {'id': 1, 'region': 'North'},
        {'id': 1, 'region': 'South'},
        {'id': 1, 'region': 'North'},  # duplicate
    ]
    result = distinct(data, ['id', 'region'])
    assert result == [
        {'id': 1, 'region': 'North'},
        {'id': 1, 'region': 'South'}
    ]

def test_distinct_missing_key_raises():
    data = [{'id': 1}, {'name': 'Bob'}]
    with pytest.raises(KeyError) as excinfo:
        distinct(data, 'name')
    assert "Missing key 'name'" in str(excinfo.value)

def test_distinct_empty_input():
    assert distinct([], 'id') == []

def test_distinct_preserves_original_rows():
    data = [{'id': 1}, {'id': 1}]
    result = distinct(data, 'id')
    assert data == [{'id': 1}, {'id': 1}]
    assert result == [{'id': 1}]
