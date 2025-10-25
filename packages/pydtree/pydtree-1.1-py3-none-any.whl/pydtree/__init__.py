"""
pydtree
-------

A Python library for generating tree views of data structures.

Usage
-----

.. code-block:: python

    from pydtree import tree

    data = {
        'root': {
            'child1': 'value1',
            'child2': 'value2'
        }
    }

    for line in tree('My Tree', data):
        print(line)
"""

from . import themes, types
from .tree import tree

__all__ = [
    'types',
    'themes',
    'tree',
]
