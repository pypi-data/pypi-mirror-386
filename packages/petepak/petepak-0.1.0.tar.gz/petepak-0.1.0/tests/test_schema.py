from petepak.listql import schema

def test_schema_single_type():
    data = [{'id': 1, 'name': 'Alice', 'score': 95.5}, {'id': 2, 'name': 'Bob', 'score': 88.0}]
    assert schema(data) == {'id': ['int'], 'name': ['str'], 'score': ['float']}

def test_schema_multiple_types():
    data = [{'id': 1, 'score': 90}, {'id': '2', 'score': '85'}, {'id': 3, 'score': None}]
    result = schema(data)
    assert set(result['id']) == {'int', 'str'}
    assert set(result['score']) == {'int', 'str', 'NoneType'}

def test_schema_missing_keys():
    data = [{'id': 1, 'name': 'Alice'}, {'id': 2}, {'id': 3, 'name': None}]
    result = schema(data)
    assert set(result['name']) == {'str', 'NoneType'}

def test_schema_empty():
    assert schema([]) == {}

def test_schema_all_none():
    data = [{'x': None}, {'x': None}]
    assert schema(data) == {'x': ['NoneType']}

def test_schema_mixed_and_missing():
    data = [{'a': 1}, {'a': '1'}, {}, {'a': None}]
    assert set(schema(data)['a']) == {'int', 'str', 'NoneType'}
