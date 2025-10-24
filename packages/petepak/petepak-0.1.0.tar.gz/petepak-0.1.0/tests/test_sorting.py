import pytest

from petepak.sorting import bubble_sort,merge_sort,quick_sort

__author__ = "Pete Bernard"
__copyright__ = "Peter Bernard"
__license__ = "MIT"
# $env:PYTHONPATH="src"; pytest tests/test_bubble_sort.py


@pytest.mark.parametrize("sort_func", [bubble_sort, merge_sort, quick_sort])
def test_basic_sort(sort_func):
    assert sort_func([3, 1, 2]) == [1, 2, 3]
    assert sort_func([], reverse=True) == []

@pytest.mark.parametrize("sort_func", [bubble_sort, merge_sort, quick_sort])
def test_sort_with_key(sort_func):
    data = [{'val': 3}, {'val': 1}, {'val': 2}]
    expected = [{'val': 1}, {'val': 2}, {'val': 3}]
    assert sort_func(data, key=lambda x: x['val']) == expected

@pytest.mark.parametrize("sort_func", [bubble_sort, merge_sort, quick_sort])
def test_sort_with_key_reverse(sort_func):
    data = [{'val': 3}, {'val': 1}, {'val': 2}]
    expected = [{'val': 3}, {'val': 2}, {'val': 1}]
    assert sort_func(data, key=lambda x: x['val'], reverse=True) == expected

@pytest.mark.parametrize("sort_func", [bubble_sort, merge_sort, quick_sort])
def test_already_sorted(sort_func):
    data = [1, 2, 3, 4]
    assert sort_func(data) == [1, 2, 3, 4]

@pytest.mark.parametrize("sort_func", [bubble_sort, merge_sort, quick_sort])
def test_sort_with_duplicates(sort_func):
    data = [3, 1, 2, 2, 1]
    expected = [1, 1, 2, 2, 3]
    assert sort_func(data) == expected

class Box:
    def __init__(self, size): self.size = size
    def __repr__(self): return f"Box({self.size})"
    def __lt__(self, other): return self.size < other.size
    def __eq__(self, other): return self.size == other.size

@pytest.mark.parametrize("sort_func", [bubble_sort, merge_sort, quick_sort])
def test_sort_custom_objects(sort_func):
    data = [Box(3), Box(1), Box(2)]
    expected = [Box(1), Box(2), Box(3)]
    assert sort_func(data, key=lambda x: x.size) == expected

@pytest.mark.parametrize("sort_func", [bubble_sort, merge_sort, quick_sort])
def test_empty_input(sort_func):
    assert sort_func([]) == []

class Unsortable: pass

@pytest.mark.parametrize("sort_func", [bubble_sort, merge_sort, quick_sort])
def test_unsortable_objects(sort_func):
    data = [Unsortable(), Unsortable()]
    with pytest.raises(TypeError):
        sort_func(data)

@pytest.mark.parametrize("sort_func,input_data", [
    (bubble_sort, 123),
    (merge_sort, [1, 'a', 3]),
    (quick_sort, [{}, object()])
])
def test_sort_invalid_input(sort_func, input_data):
    with pytest.raises(TypeError):
        sort_func(input_data)
