"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = petepak.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This file can be renamed depending on your needs or safely removed if not needed.

References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import logging
import sys
from collections.abc import Iterable
from typing import Callable, Any

from petepak import __version__

__author__ = "Peter Bernard"
__copyright__ = "Peter Bernard"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from petepak.skeleton import fib`,
# when using this Python module as a library.


def bubble_sort(obj: Iterable,key: Callable[[Any], Any] = lambda x: x, reverse: bool = False
) -> list:
    """
    Sorts an iterable using bubble sort.

    Parameters:
    - obj: An iterable of elements to sort.
    - key: A function that extracts a comparison key from each element.
    - reverse: If True, sort in descending order.

    Returns:
    - A sorted list of elements.

    Raises:
    - TypeError: If obj is not iterable or contains non-comparable elements.
    """
    # print("Time Complexity: Best: O(n), Worst: O(n^2), Average: O(n^2)\nSpace Complexity: O(1)")
    if not isinstance(obj, Iterable):
        raise TypeError("obj must be an iterable")

    arr = list(obj)

    try:
        _ = [key(x) for x in arr]  # Validate key function and comparability
    except Exception as e:
        raise TypeError(f"Elements must be comparable using key: {e}")

    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            a, b = key(arr[j]), key(arr[j + 1])
            if (a > b) != reverse:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break

    return arr

def merge_sort(
    obj: Iterable,
    key: Callable[[Any], Any] = lambda x: x,
    reverse: bool = False) -> list:
    """
    Sorts an iterable using merge sort.

    Parameters:
    - obj: An iterable of elements to sort.
    - key: A function that extracts a comparison key from each element.
    - reverse: If True, sort in descending order.

    Returns:
    - A sorted list of elements.

    Raises:
    - TypeError: If obj is not iterable or contains non-comparable elements.
    """
    # print("Time Complexity: Best: O(n log n), Worst: O(n log n), Average: O(n log n)\nSpace Complexity: O(n)")
    if not isinstance(obj, Iterable):
        raise TypeError("obj must be an iterable")

    arr = list(obj)

    try:
        _ = [key(x) for x in arr]  # Validate key function and comparability
    except Exception as e:
        raise TypeError(f"Elements must be comparable using key: {e}")

    def merge(left, right):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            a, b = key(left[i]), key(right[j])
            if (a <= b) != reverse:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    def sort(sublist):
        if len(sublist) <= 1:
            return sublist
        mid = len(sublist) // 2
        left = sort(sublist[:mid])
        right = sort(sublist[mid:])
        return merge(left, right)

    return sort(arr)
    
def quick_sort(
    obj: Iterable,
    key: Callable[[Any], Any] = lambda x: x,
    reverse: bool = False) -> list:
    """
    Sorts an iterable using quick sort.

    Parameters:
    - obj: An iterable of elements to sort.
    - key: A function that extracts a comparison key from each element.
    - reverse: If True, sort in descending order.

    Returns:
    - A sorted list of elements.

    Raises:
    - TypeError: If obj is not iterable or contains non-comparable elements.
    """
    # print("Time Complexity: Best: O(n log n), Worst: O(n^2), Average: O(n log n)\nSpace Complexity: O(log n)")
    if not isinstance(obj, Iterable):
        raise TypeError("obj must be an iterable")

    arr = list(obj)

    try:
        _ = [key(x) for x in arr]  # Validate key function and comparability
    except Exception as e:
        raise TypeError(f"Elements must be comparable using key: {e}")

    def sort(sublist):
        if len(sublist) <= 1:
            return sublist
        pivot = sublist[0]
        pivot_key = key(pivot)
        left = [x for x in sublist[1:] if (key(x) < pivot_key) != reverse]
        right = [x for x in sublist[1:] if (key(x) >= pivot_key) != reverse]
        return sort(left) + [pivot] + sort(right)

    return sort(arr)    









# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version=f"petepak {__version__}",
    )
    parser.add_argument(dest="n", help="n-th Fibonacci number", type=int, metavar="INT")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args):
    """Wrapper allowing :func:`fib` to be called with string arguments in a CLI fashion

    Instead of returning the value from :func:`fib`, it prints the result to the
    ``stdout`` in a nicely formatted message.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    _logger.debug("Starting crazy calculations...")
    print(f"The {args.n}-th Fibonacci number is {fib(args.n)}")
    _logger.info("Script ends here")


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m petepak.skeleton 42
    #
    run()
