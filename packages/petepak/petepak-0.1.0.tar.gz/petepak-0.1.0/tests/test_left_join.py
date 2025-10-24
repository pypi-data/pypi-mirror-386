import pytest
from petepak.listql import left_join


def test_left_join_on_id(list1, list2):
    result = left_join(list1, list2, expr="a.id == b.id")
    assert result == [
        {
            'list1_id': 1, 'list1_name': 'Alice', 'list1_age': 25,
            'list2_id': 1, 'list2_score': 90
        },
        {
            'list1_id': 2, 'list1_name': 'Bob', 'list1_age': 30,
            'list2_id': 2, 'list2_score': 85
        },
        {
            'list1_id': 3, 'list1_name': 'Charlie', 'list1_age': 35,
            'list2_id': None, 'list2_score': None
        }
    ]

def test_left_join_with_additional_condition(list1, list2):
    result = left_join(list1, list2, expr="a.id == b.id and a.age < 30")
    assert result == [
        {
            'list1_id': 1, 'list1_name': 'Alice', 'list1_age': 25,
            'list2_id': 1, 'list2_score': 90
        },
        {
            'list1_id': 2, 'list1_name': 'Bob', 'list1_age': 30,
            'list2_id': None, 'list2_score': None
        },
        {
            'list1_id': 3, 'list1_name': 'Charlie', 'list1_age': 35,
            'list2_id': None, 'list2_score': None
        }
    ]

def test_left_join_no_matches(list1, list2):
    result = left_join(list1, list2, expr="a.id == b.id and a.age > 100")
    assert all(row['list2_id'] is None for row in result)

def test_left_join_on_non_id_field():
    l1 = [{'name': 'Alice'}, {'name': 'Bob'}]
    l2 = [{'name': 'Bob'}, {'name': 'Charlie'}]
    result = left_join(l1, l2, expr="a.name == b.name")
    assert result == [
        {'list1_name': 'Alice', 'list2_name': None},
        {'list1_name': 'Bob', 'list2_name': 'Bob'}
    ]

def test_left_join_with_custom_prefixes():
    l1 = [{'id': 1}]
    l2 = [{'id': 1}]
    result = left_join(l1, l2, expr="a.id == b.id", list1_name='left', list2_name='right')
    assert result == [
        {'left_id': 1, 'right_id': 1}
    ]

def test_left_join_invalid_expression_raises():
    l1 = [{'id': 1}]
    l2 = [{'id': 1}]
    with pytest.raises(ValueError):
        left_join(l1, l2, expr="a.id === b.id")