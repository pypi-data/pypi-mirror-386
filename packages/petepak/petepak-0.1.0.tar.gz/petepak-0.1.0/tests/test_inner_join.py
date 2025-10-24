import pytest
from petepak.listql import inner_join


def test_inner_join_on_id(list1, list2):
    result = inner_join(list1, list2, expr="a.id == b.id")
    assert len(result) == 2

def test_inner_join_with_condition(list1, list2):
    result = inner_join(list1, list2, expr="a.id == b.id and a.age > 25")
    assert len(result) == 1

def test_inner_join_no_matches(list1, list2):
    result = inner_join(list1, list2, expr="a.id == b.id and a.age > 100")
    assert result == []

def test_inner_join_non_id_field():
    l1 = [{'name': 'Alice'}, {'name': 'Bob'}]
    l2 = [{'name': 'Bob'}, {'name': 'Charlie'}]
    result = inner_join(l1, l2, expr="a.name == b.name")
    assert result == [{'list1_name': 'Bob', 'list2_name': 'Bob'}]

def test_inner_join_custom_prefixes():
    l1 = [{'id': 1}]
    l2 = [{'id': 1}]
    result = inner_join(l1, l2, expr="a.id == b.id", list1_name='left', list2_name='right')
    assert result == [{'left_id': 1, 'right_id': 1}]

def test_inner_join_invalid_expression():
    with pytest.raises(ValueError):
        inner_join([{'id': 1}], [{'id': 1}], expr="a.id === b.id")
