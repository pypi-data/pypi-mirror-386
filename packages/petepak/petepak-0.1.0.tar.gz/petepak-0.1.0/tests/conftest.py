"""
    Dummy conftest.py for petepak.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    - https://docs.pytest.org/en/stable/fixture.html
    - https://docs.pytest.org/en/stable/writing_plugins.html
"""

import pytest
@pytest.fixture
def list1():
    return [
        {'id': 1, 'name': 'Alice', 'age': 25},
        {'id': 2, 'name': 'Bob', 'age': 30},
        {'id': 3, 'name': 'Charlie', 'age': 35}
    ]

@pytest.fixture
def list2():
    return [
        {'id': 1, 'score': 90},
        {'id': 2, 'score': 85},
        {'id': 4, 'score': 70}
    ]
