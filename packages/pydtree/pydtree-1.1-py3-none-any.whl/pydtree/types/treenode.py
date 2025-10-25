from dataclasses import dataclass
from typing import Any, List


@dataclass
class TreeNode:
    """A node in a tree."""
    value: Any
    children: List['TreeNode'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []
