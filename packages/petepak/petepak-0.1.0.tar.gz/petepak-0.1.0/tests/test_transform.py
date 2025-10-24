import pytest
from petepak.listql import transform  # Adjust import path if needed

def test_transform_single_column():
    data = [{'score': 95}, {'score': 80}, {'score': 60}]
    result = transform(data, 'label', lambda r: 'high' if r['score'] > 85 else 'low')
    assert result == [
        {'score': 95, 'label': 'high'},
        {'score': 80, 'label': 'low'},
        {'score': 60, 'label': 'low'}
    ]
    assert data == [{'score': 95}, {'score': 80}, {'score': 60}]  # original unchanged

def test_transform_multiple_columns():
    data = [{'name': 'Alice', 'score': 90}, {'name': 'Bob', 'score': 70}]
    result = transform(data, {
        'label': lambda r: 'pass' if r['score'] >= 75 else 'fail',
        'upper_name': lambda r: r['name'].upper()
    })
    assert result == [
        {'name': 'Alice', 'score': 90, 'label': 'pass', 'upper_name': 'ALICE'},
        {'name': 'Bob', 'score': 70, 'label': 'fail', 'upper_name': 'BOB'}
    ]

def test_transform_handles_exceptions():
    data = [{'value': '10'}, {'value': 'x'}]
    result = transform(data, 'int_value', lambda r: int(r['value']))
    assert result == [
        {'value': '10', 'int_value': 10},
        {'value': 'x', 'int_value': None}
    ]

def test_transform_empty_input():
    result = transform([], 'new_col', lambda r: 123)
    assert result == []

def test_transform_preserves_original_rows():
    data = [{'a': 1}, {'a': 2}]
    result = transform(data, 'b', lambda r: r['a'] * 10)
    assert data == [{'a': 1}, {'a': 2}]
    assert result == [{'a': 1, 'b': 10}, {'a': 2, 'b': 20}]
