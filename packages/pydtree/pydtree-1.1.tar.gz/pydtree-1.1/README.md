# DTree: Python Library for Generating Text Tree Representations

pydtree is a Python library for creating textual visualizations of hierarchical data structures such as dictionaries, lists, sets, and tuples. It allows generating beautiful tree-like representations of data with support for various themes and customization.

## Features

- Create trees from dictionaries, lists, tuples, sets, and other data types
- Support for different themes: ASCII, Unicode, and custom
- Customizable rendering via render functions
- Data filtering via filter functions
- Generator-based output for efficient handling of large data

## Installation

Install the library using pip:

```bash
pip install pydtree
```

## Usage

### Basic Example

```python
from pydtree import tree

# Data as a dictionary
data = {
    'root': {
        'child1': 'value1',
        'child2': 'value2',
        'child3': {
            'grandchild1': 'value3',
            'grandchild2': 'value4'
        }
    }
}

# Generate and print the tree
for line in tree('My Tree', data):
    print(line)
```

Output:
```
My Tree:
`-- root
    +-- child1: value1
    +-- child2: value2
    `-- child3
        +-- grandchild1: value3
        `-- grandchild2: value4
```

### Example with List

```python
data_list = {
    'root': [
        'item1',
        'item2',
        {'nested': 'value'}
    ]
}

for line in tree('List Tree', data_list):
    print(line)
```

Output:
```
List Tree:
`-- root
    +-- [0]: item1
    +-- [1]: item2
    `-- [2]
        `-- nested: value
```

### Example with Set

```python
data_set = {
    'root': {'a', 'b', 'c'}
}

for line in tree('Set Tree', data_set):
    print(line)
```

Output:
```
Set Tree:
`-- root
    +-- a
    +-- b
    `-- c
```

## Themes

The library supports various themes for displaying the tree.

### ASCII Theme (Default)

```python
from pydtree import tree, themes

for line in tree('ASCII Theme', data, theme=themes.Ascii):
    print(line)
```

Output:
```
ASCII Theme:
`-- root
    +-- child1: value1
    +-- child2: value2
    `-- child3
        +-- grandchild1: value3
        `-- grandchild2: value4
```

### Unicode Theme

```python
for line in tree('Unicode Theme', data, theme=themes.Unicode):
    print(line)
```

Output:
```
Unicode Theme:
└── root
    ├── child1: value1
    ├── child2: value2
    └── child3
        ├── grandchild1: value3
        └── grandchild2: value4
```

### Custom Theme

You can create your own theme by defining a Theme object:

```python
from pydtree.types import Theme

MyTheme = Theme(
    vertical='|   ',
    branch='|- ',
    corner='=- ',
    tab='    '
)

for line in tree('Custom Theme', data, theme=MyTheme):
    print(line)
```

Output:
```
Custom Theme:
=- root
    |- child1: value1
    |- child2: value2
    =- child3
        |- grandchild1: value3
        =- grandchild2: value4
```

## Customization

### Custom Rendering

You can customize the display of nodes using a render function:

```python
from typing import Any
from pydtree import tree
from pydtree.types import RenderData

def custom_render(key: str, value: Any, render_data: RenderData) -> str:
    if render_data.is_endpoint:  # If the node is an endpoint
        if isinstance(value, str):
            return f"{key}: \"{value}\""
        elif isinstance(value, int):
            ...

    else:  # If the node is not an endpoint
        if isinstance(value, dict):
            return f"{key}: (dict with {len(value)} keys)"
        elif isinstance(value, list):
            ...

data = {
    'root': {
        'child1': 'value1',
        'child2': ['a', 'b', 'c'],
        'child3': {'nested': 42}
    }
}

for line in tree('My Tree', data, render=custom_render):
    print(line)
```

Output:
```
My Tree:
`-- root
    +-- child1: "value1"
    +-- child2: (list with 3 items)
    |   +-- [0]: "a"
    |   +-- [1]: "b"
    |   `-- [2]: "c"
    `-- child3: (dict with 1 keys)
        `-- nested: 42
```

### Data Filtering

Use a filter function to filter or modify data before rendering:

```python
from typing import Any, Tuple

def filter_func(key: str, value: Any) -> Tuple[str, Any]:
    if key.startswith("_"):
        return None, None  # Exclude nodes starting with "_"

    if key in {"password", "secret", "token"}:
        return key, "******"  # Mask sensitive data

    return key, value  # Return the default data (MANDATORY)


data = {
    'root': {
        '_root_child1': 'value1',
        '_root_child2': 'value2',
        'child1': 'value1',
        'child2': 'value2',
        'child3': {
            'grandchild1': 'value3',
            'grandchild2': 'value4'
        },
        'password': 'password'
    }
}

for line in tree('Filtered Tree', data, filter=filter_func):
    print(line)
```

Output:
```
Filtered Tree:
`-- root
    +-- child1: value1
    +-- child2: value2
    +-- child3
    |   +-- grandchild1: value3
    |   `-- grandchild2: value4
    `-- password: ******
```

## API

### Main Function

```python
def tree(
    name: str,
    data: Any,
    theme: Theme = themes.Ascii,
    render: Callable[[str, Any, RenderData], str] = default_render,
    filter: Callable[[str, Any], Any] = default_filter,
) -> Generator[str, None, None]:
```

- **name**: Tree name (string).
- **data**: Input data (dict, list, tuple, set, frozenset, str, int, float, bool).
- **theme**: Theme for rendering (Theme, default Ascii).
- **render**: Function for rendering each node (Callable).
- **filter**: Function for filtering data (Callable).

Returns a generator of strings, each being a line of the tree.

### Types

- **Theme**: Class for defining themes (vertical, branch, corner, tab).
- **TreeNode**: Tree node (value, children).
- **RenderData**: Rendering data (is_endpoint).

### Themes

- **themes.Ascii**: ASCII characters.
- **themes.Unicode**: Unicode characters.

## License

pydtree is licensed under the MIT License.

## Contributing

If you'd like to contribute to pydtree, please fork the repository and submit a pull request.