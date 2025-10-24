import pytest
from petepak.listql import join

def test_inner_join_dispatch(list1, list2):
    result = join(list1, list2, expr="a.id == b.id", join_type="inner")
    assert len(result) == 2
    assert all("list1_id" in row and "list2_id" in row for row in result)

def test_left_join_dispatch(list1, list2):
    result = join(list1, list2, expr="a.id == b.id", join_type="left")
    assert len(result) == 3
    assert any(row["list2_id"] is None for row in result)

def test_right_join_dispatch(list1, list2):
    result = join(list1, list2, expr="a.id == b.id", join_type="right")
    assert len(result) == 3
    assert any(row["list1_id"] is None for row in result)

def test_outer_join_dispatch(list1, list2):
    result = join(list1, list2, expr="a.id == b.id", join_type="outer")
    assert len(result) == 4
    assert any(row["list1_id"] is None or row["list2_id"] is None for row in result)

def test_custom_prefixes(list1, list2):
    result = join(list1, list2, expr="a.id == b.id", join_type="inner", list1_name="left", list2_name="right")
    assert all("left_id" in row and "right_id" in row for row in result)

def test_invalid_join_type_raises(list1, list2):
    with pytest.raises(ValueError):
        join(list1, list2, expr="a.id == b.id", join_type="diagonal")

def test_invalid_expression_raises(list1, list2):
    with pytest.raises(ValueError):
        join(list1, list2, expr="a.id === b.id", join_type="inner")