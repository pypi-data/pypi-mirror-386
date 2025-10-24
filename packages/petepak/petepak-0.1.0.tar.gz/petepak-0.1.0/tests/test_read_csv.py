import pytest
import tempfile
import os
from petepak.listql import read_csv  # Adjust import path as needed

def write_temp_csv(content):
    """Helper to write CSV content to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".csv", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def test_read_csv_with_header_and_schema():
    content = "id,name,score\n1,Alice,95.5\n2,Bob,88.0"
    path = write_temp_csv(content)
    schema = {'id': int, 'score': float}
    result = read_csv(path, schema=schema)
    assert result == [
        {'id': 1, 'name': 'Alice', 'score': 95.5},
        {'id': 2, 'name': 'Bob', 'score': 88.0}
    ]
    os.remove(path)

def test_read_csv_without_header_with_schema():
    content = "1,Alice,95.5\n2,Bob,88.0"
    path = write_temp_csv(content)
    schema = {'id': int, 'score': float}
    result = read_csv(path, header=False, header_list=['id', 'name', 'score'], schema=schema)
    assert result == [
        {'id': 1, 'name': 'Alice', 'score': 95.5},
        {'id': 2, 'name': 'Bob', 'score': 88.0}
    ]
    os.remove(path)

def test_read_csv_with_custom_separator_and_schema():
    content = "id|name|score\n1|Alice|95.5\n2|Bob|88.0"
    path = write_temp_csv(content)
    schema = {'id': int, 'score': float}
    result = read_csv(path, separator='|', schema=schema)
    assert result[0]['score'] == 95.5
    assert result[1]['id'] == 2
    os.remove(path)

def test_read_csv_with_invalid_casting():
    content = "id,name,score\n1,Alice,95.5\n2,Bob,not_a_number"
    path = write_temp_csv(content)
    schema = {'id': int, 'score': float}
    result = read_csv(path, schema=schema)
    assert result[1]['score'] is None  # casting failed
    os.remove(path)

def test_read_csv_with_empty_string_casts_to_none():
    content = "id,name,score\n1,Alice,95.5\n2,Bob,"
    path = write_temp_csv(content)
    schema = {'score': float}
    result = read_csv(path, schema=schema)
    assert result[1]['score'] is None
    os.remove(path)

def test_read_csv_without_header_missing_header_list_raises():
    content = "1,Alice,95.5\n2,Bob,88.0"
    path = write_temp_csv(content)
    with pytest.raises(ValueError):
        read_csv(path, header=False)
    os.remove(path)

def test_read_csv_empty_file():
    path = write_temp_csv("")
    result = read_csv(path)
    assert result == []
    os.remove(path)

def test_read_csv_with_partial_schema():
    content = "id,name,score\n1,Alice,95.5\n2,Bob,88.0"
    path = write_temp_csv(content)
    schema = {'score': float}
    result = read_csv(path, schema=schema)
    assert result[0]['score'] == 95.5
    assert result[0]['id'] == '1'  # not cast
    os.remove(path)
