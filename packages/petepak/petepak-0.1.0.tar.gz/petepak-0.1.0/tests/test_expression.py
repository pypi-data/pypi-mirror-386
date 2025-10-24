import pytest
from petepak.listql import expression_to_lambda

@pytest.mark.parametrize("expr,a,b,expected", [
    ("a.id == b.id", {'id': 1}, {'id': 1}, True),
    ("a.id != b.id", {'id': 1}, {'id': 2}, True),
    ("a.score < b.score", {'score': 50}, {'score': 90}, True),
    ("a.score >= b.score", {'score': 90}, {'score': 90}, True),
    ("a.name == b.name and a.age < b.age", {'name': 'Alice', 'age': 25}, {'name': 'Alice', 'age': 30}, True),
    ("a.name != b.name or a.age > b.age", {'name': 'Alice', 'age': 35}, {'name': 'Bob', 'age': 30}, True),
])
def test_valid_expressions(expr, a, b, expected):
    assert expression_to_lambda(expr)(a, b) == expected

def test_missing_keys():
    f = expression_to_lambda("a.id == b.id")
    assert f({}, {'id': 1}) is False
    assert f({'id': 1}, {}) is False

@pytest.mark.parametrize("expr", [
    "a.id === b.id",
    "a.id == b.id;",
    "a.id == b.id and exec('x')",
    "a.id == b.id or __import__('os').system('rm -rf /')",
    "a.id == b.id and a.age < b.age # comment",
])
def test_invalid_expressions(expr):
    with pytest.raises(ValueError):
        expression_to_lambda(expr)

def test_expression_with_parentheses():
    f = expression_to_lambda("(a.id == b.id) and (a.age < b.age)")
    assert f({'id': 1, 'age': 25}, {'id': 1, 'age': 30}) is True

def test_expression_with_quotes():
    f = expression_to_lambda("a.name == b.name")
    assert f({'name': "Alice"}, {'name': "Alice"}) is True
