import pytest
from petepak.listql import outer_join

def test_outer_join_basic_match(list1, list2):
    result = outer_join(list1, list2, expr="a.id == b.id")
    assert len(result) == 4
    assert any(row['list1_name'] is None for row in result)  # b.id = 4
    assert any(row['list2_score'] is None for row in result)  # a.id = 3

def test_outer_join_with_condition(list1, list2):
    result = outer_join(list1, list2, expr="a.id == b.id and b.score > 85")
    assert len(result) == 5  # 1 match + 2 unmatched from list1 + 2 unmatched from list2

    # Matched row
    assert any(row['list1_name'] == 'Alice' and row['list2_score'] == 90 for row in result)

    # Unmatched from list1
    assert any(row['list1_name'] == 'Bob' and row['list2_score'] is None for row in result)
    assert any(row['list1_name'] == 'Charlie' and row['list2_score'] is None for row in result)

    # Unmatched from list2
    assert any(row['list1_name'] is None and row['list2_score'] == 85 for row in result)
    assert any(row['list1_name'] is None and row['list2_score'] == 70 for row in result)


def test_outer_join_no_matches(list1, list2):
    result = outer_join(list1, list2, expr="a.id == b.id and b.score < 50")
    assert len(result) == 6  # All unmatched: 3 from list1, 3 from list2
    assert all(row['list1_name'] is None or row['list2_score'] is None for row in result)


def test_outer_join_custom_prefixes(list1, list2):
    result = outer_join(list1, list2, expr="a.id == b.id", list1_name="left", list2_name="right")
    assert all("left_name" in row and "right_score" in row for row in result)
    
    
