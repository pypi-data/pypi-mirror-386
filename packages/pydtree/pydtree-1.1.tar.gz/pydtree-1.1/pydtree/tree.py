from typing import Any, Generator, Callable

from . import themes
from .types import TreeNode, Theme, RenderData


def default_render(key: str, value: Any, render_data: RenderData) -> str:
    if render_data.is_endpoint:
        return f'{key}: {value}'
    else:
        return f'{key}'


def default_filter(key: str, value: Any) -> Any:
    return key, value


def tree(
    name: str,
    data: Any,
    max_depth: int = 10,
    theme: Theme = themes.Ascii,
    render: Callable[[str, Any, RenderData], str] = default_render,
    filter: Callable[[str, Any], Any] = default_filter,
) -> Generator[str, None, None]:
    """
    Generates a tree view of the input data.

    Args:
        name: Tree name.
        data: Input data.
        max_depth: Maximum depth of the tree.
        theme: Theme for rendering the tree.
        render: Function for rendering each node.
        filter: Function for filtering the data.
    Yields:
        str: Each line of the tree.
    """
    if not isinstance(data, (dict, list, tuple, set, frozenset, str, int, float, bool)):
        raise TypeError('Data must be a dict, list, tuple, set, frozenset, str, int, float, or bool')

    def _build_tree(data: Any, parent_key: str = '', depth: int = 0) -> TreeNode:
        """
        Recursively builds a tree from the input data.
        """
        if max_depth > 0 and depth >= max_depth:
            return None

        if parent_key:
            depth += 1
            parent_key, data = filter(parent_key, data)

        if parent_key is None or data is None:
            return None

        node = TreeNode(value=parent_key)
        is_endpoint = isinstance(data, (str, int, float, bool))

        if parent_key:
            node.value = render(parent_key, data, RenderData(is_endpoint=is_endpoint))

        if isinstance(data, dict):
            for key, value in data.items():
                child = _build_tree(value, str(key), depth)
                if child:
                    node.children.append(child)

        elif isinstance(data, (list, tuple, set, frozenset)):
            for idx, item in enumerate(data):
                child = _build_tree(item, f'[{idx}]', depth)
                if child:
                    node.children.append(child)

        return node

    root = _build_tree(data)
    yield f'{name}:'

    def _traverse(
        node: TreeNode,
        prefix: str = '',
        is_last: bool = True
    ) -> Generator[str, None, None]:
        if prefix:
            connector = theme.corner if is_last else theme.branch
            line = prefix + connector + node.value
        else:
            line = node.value
        if prefix:
            yield line[len(theme.tab):]
        else:
            yield line

        new_prefix = prefix + (theme.tab if is_last else theme.vertical)
        for i, child in enumerate(node.children):
            yield from _traverse(
                child,
                new_prefix,
                i == len(node.children) - 1
            )

    yield from _traverse(root)
