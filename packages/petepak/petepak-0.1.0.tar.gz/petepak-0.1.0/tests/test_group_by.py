import pytest
from petepak.listql import group_by  # Adjust import path as needed

def test_group_by_single_key():
    data = [
        {'id': 1, 'group': 'A'},
        {'id': 2, 'group': 'B'},
        {'id': 3, 'group': 'A'}
    ]
    result = group_by(data, 'group')
    groups = [sorted(group, key=lambda r: r['id']) for group in result]
    assert sorted(groups, key=lambda g: g[0]['group']) == [
        [{'id': 1, 'group': 'A'}, {'id': 3, 'group': 'A'}],
        [{'id': 2, 'group': 'B'}]
    ]
    assert data == [
        {'id': 1, 'group': 'A'},
        {'id': 2, 'group': 'B'},
        {'id': 3, 'group': 'A'}
    ]  # original unchanged

def test_group_by_multiple_keys():
    data = [
        {'id': 1, 'year': 2020, 'region': 'North'},
        {'id': 2, 'year': 2020, 'region': 'South'},
        {'id': 3, 'year': 2021, 'region': 'North'},
        {'id': 4, 'year': 2020, 'region': 'North'}
    ]
    result = group_by(data, ['year', 'region'])
    group_keys = [set((row['year'], row['region']) for row in group) for group in result]
    assert set.union(*group_keys) == {(2020, 'North'), (2020, 'South'), (2021, 'North')}
    assert any(len(group) == 2 for group in result)  # (2020, North) group

def test_group_by_missing_key_raises():
    data = [{'id': 1, 'group': 'A'}, {'id': 2}]
    with pytest.raises(KeyError) as excinfo:
        group_by(data, 'group')
    assert "Missing key 'group'" in str(excinfo.value)

def test_group_by_empty_input():
    result = group_by([], 'group')
    assert result == []

def test_group_by_preserves_row_data():
    data = [{'id': 1, 'group': 'X'}]
    result = group_by(data, 'group')
    assert result == [[{'id': 1, 'group': 'X'}]]
    assert data == [{'id': 1, 'group': 'X'}]  # original unchanged
