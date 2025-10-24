import pytest
from petepak.listql import order_by  # Adjust import path if needed

def test_order_by_single_key():
    data = [{'score': 90}, {'score': 70}, {'score': 80}]
    result = order_by(data, 'score')
    assert result == [{'score': 70}, {'score': 80}, {'score': 90}]

def test_order_by_multiple_keys():
    data = [
        {'region': 'North', 'score': 80},
        {'region': 'South', 'score': 90},
        {'region': 'North', 'score': 70}
    ]
    result = order_by(data, ['region', 'score'])
    assert result == [
        {'region': 'North', 'score': 70},
        {'region': 'North', 'score': 80},
        {'region': 'South', 'score': 90}
    ]

def test_order_by_reverse():
    data = [{'score': 90}, {'score': 70}, {'score': 80}]
    result = order_by(data, 'score', reverse=True)
    assert result == [{'score': 90}, {'score': 80}, {'score': 70}]

def test_order_by_custom_function():
    data = [{'name': 'Alice'}, {'name': 'Bob'}, {'name': 'Charlie'}]
    result = order_by(data, lambda r: len(r['name']))
    assert result == [{'name': 'Bob'}, {'name': 'Alice'}, {'name': 'Charlie'}]

def test_order_by_missing_keys():
    data = [{'score': 90}, {}, {'score': 80}]
    result = order_by(data, 'score')
    assert result == [{}, {'score': 80}, {'score': 90}]

def test_order_by_empty_input():
    assert order_by([], 'score') == []

def test_order_by_preserves_original():
    data = [{'score': 90}, {'score': 70}]
    result = order_by(data, 'score')
    assert data == [{'score': 90}, {'score': 70}]
