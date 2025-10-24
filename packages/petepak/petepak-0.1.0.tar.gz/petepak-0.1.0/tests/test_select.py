import pytest
from petepak.listql import select  # Adjust import path as needed

def test_select_basic_columns():
    data = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
    result = select(data, ['id'])
    assert result == [{'id': 1}, {'id': 2}]
    assert data == [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]  # original unchanged

def test_select_multiple_columns():
    data = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
    result = select(data, ['id', 'name'])
    assert result == [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]

def test_select_missing_column_raises_error():
    data = [{'id': 1}, {'name': 'Bob'}]
    with pytest.raises(KeyError) as excinfo:
        select(data, ['id', 'name'])
    assert "Missing column 'name' in row 0" in str(excinfo.value) or "Missing column 'id' in row 1" in str(excinfo.value)

def test_select_empty_column_list():
    data = [{'id': 1, 'name': 'Alice'}]
    result = select(data, [])
    assert result == [{}]

def test_select_preserves_row_order():
    data = [{'id': 2}, {'id': 1}, {'id': 3}]
    result = select(data, ['id'])
    assert result == [{'id': 2}, {'id': 1}, {'id': 3}]
    
