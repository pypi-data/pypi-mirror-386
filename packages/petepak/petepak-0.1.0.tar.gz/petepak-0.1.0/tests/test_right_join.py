import pytest
from petepak.listql import right_join


def test_right_join_basic_match(list1, list2):
    result = right_join(list1, list2, expr="a.id == b.id")
    assert len(result) == 3
    assert result[0]['list1_name'] == 'Alice'
    assert result[2]['list1_name'] is None  # unmatched b.id = 4

def test_right_join_with_condition(list1, list2):
    result = right_join(list1, list2, expr="a.id == b.id and b.score > 85")
    assert len(result) == 3
    assert result[0]['list1_name'] == 'Alice'
    assert result[1]['list1_name'] is None  # b.score = 85 fails condition
    assert result[2]['list1_name'] is None  # unmatched id

def test_right_join_no_matches(list1, list2):
    result = right_join(list1, list2, expr="a.id == b.id and b.score < 50")
    assert all(row['list1_name'] is None for row in result)

def test_right_join_custom_prefixes(list1, list2):
    result = right_join(list1, list2, expr="a.id == b.id", list1_name="left", list2_name="right")
    assert all("left_name" in row and "right_score" in row for row in result)
    
