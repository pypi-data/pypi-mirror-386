import pytest
from petepak.listql import filter

# Tests for string expression filtering
def test_filter_expression_basic():
    data = [{'score': 90}, {'score': 75}, {'score': 85}]
    result = filter(data, "a.score >= 80")
    assert result == [{'score': 90}, {'score': 85}]
    assert data == [{'score': 90}, {'score': 75}, {'score': 85}]  # original unchanged

def test_filter_expression_all_pass():
    data = [{'x': 1}, {'x': 2}]
    result = filter(data, "a.x > 0")
    assert result == [{'x': 1}, {'x': 2}]

def test_filter_expression_none_pass():
    data = [{'x': -1}, {'x': -2}]
    result = filter(data, "a.x > 0")
    assert result == []

def test_filter_expression_missing_key():
    data = [{'a': 1}, {'b': 2}]
    with pytest.raises(TypeError):
        filter(data, "a.a > 0 and a.b > 0")

def test_filter_expression_invalid_syntax():
    data = [{'x': 1}]
    with pytest.raises(ValueError):
        filter(data, "a.x === 1")

def test_filter_expression_unsafe_code():
    data = [{'x': 1}]
    with pytest.raises(ValueError):
        filter(data, "a.x > 0 and __import__('os').system('rm -rf /')")

def test_filter_expression_row_order_preserved():
    data = [{'id': 3}, {'id': 1}, {'id': 2}]
    result = filter(data, "a.id != 1")
    assert result == [{'id': 3}, {'id': 2}]

# Tests for lambda function filtering
def test_filter_lambda_basic():
    data = [{'score': 90}, {'score': 75}, {'score': 85}]
    result = filter(data, lambda row: row.get('score', 0) >= 80)
    assert result == [{'score': 90}, {'score': 85}]
    assert data == [{'score': 90}, {'score': 75}, {'score': 85}]  # original unchanged

def test_filter_lambda_all_pass():
    data = [{'x': 1}, {'x': 2}]
    result = filter(data, lambda row: row.get('x', 0) > 0)
    assert result == [{'x': 1}, {'x': 2}]

def test_filter_lambda_none_pass():
    data = [{'x': -1}, {'x': -2}]
    result = filter(data, lambda row: row.get('x', 0) > 0)
    assert result == []

def test_filter_lambda_missing_key():
    data = [{'a': 1}, {'b': 2}]
    result = filter(data, lambda row: row.get('a', 0) > 0 and row.get('b', 0) > 0)
    assert result == []  # No rows have both 'a' and 'b' keys

def test_filter_lambda_complex_condition():
    data = [{'name': 'Alice', 'age': 25}, {'name': 'Bob', 'age': 30}, {'name': 'Charlie', 'age': 35}]
    result = filter(data, lambda row: len(row.get('name', '')) > 3 and row.get('age', 0) < 35)
    assert result == [{'name': 'Alice', 'age': 25}]

def test_filter_lambda_row_order_preserved():
    data = [{'id': 3}, {'id': 1}, {'id': 2}]
    result = filter(data, lambda row: row.get('id', 0) != 1)
    assert result == [{'id': 3}, {'id': 2}]

def test_filter_lambda_with_none_values():
    data = [{'value': 10}, {'value': None}, {'value': 20}]
    result = filter(data, lambda row: row.get('value') is not None and row.get('value', 0) > 15)
    assert result == [{'value': 20}]

# Tests for mixed usage
def test_filter_expression_vs_lambda_same_result():
    data = [{'score': 90}, {'score': 75}, {'score': 85}]
    expr_result = filter(data, "a.score >= 80")
    lambda_result = filter(data, lambda row: row.get('score', 0) >= 80)
    assert expr_result == lambda_result

def test_filter_empty_input():
    result_expr = filter([], "a.x > 0")
    result_lambda = filter([], lambda row: row.get('x', 0) > 0)
    assert result_expr == []
    assert result_lambda == []
