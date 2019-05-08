import numpy as np
from pydm.widgets.treeview import PyDMTreeView


def test_construct(qtbot):
    tree = PyDMTreeView()
    qtbot.addWidget(tree)

    assert 'root' in tree._items
    assert 'root' in tree._visited_items

def test_parse_data(qtbot):
    first_data = {
        'node1': 'val1',
        'node2': {
            'subnode1': [0, 1, 2, 3],
            'subnode2': False,
            'subnode3': 123.45,
            'subnode4': np.ones((10, 20)),
        },
        'node3': [
            {'subnode1': {
                'subsubnode1': 'foo',
                'subsubnode2': 123.456
            }},
            {'subnode2': 43},
            {'subnode3': None}
        ]
    }
    tree = PyDMTreeView()
    qtbot.addWidget(tree)
    tree._receive_data(first_data)

    assert 'root_node1' in tree._items
    assert 'root_node3_0_subnode1_subsubnode1' in tree._items
    assert 'root_node3_1_subnode2' in tree._items

    map = [
        ('root_node1', 'val1'),
        ('root_node2_subnode1_2', '2'),
        ('root_node2_subnode4', 'Array of shape: (10, 20)'),
        ('root_node3_0_subnode1_subsubnode1', 'foo'),
        ('root_node3_1_subnode2', '43')
    ]
    for itm, val in map:
        tree_item = tree._items[itm]
        assert tree_item.text(1) == val

    new_data = {
        'node1': 'val2',
        'node2': {
            'subnode1': [4, 5, 6],
            'subnode2': True,
        },
        'node3': [
            {'subnode1': {
                'subsubnode1': 'bar',
            }},
            {'subnode3': 1}
        ]
    }

    tree._receive_data(new_data)
    assert 'root_node1' in tree._items
    assert 'root_node3_1_subnode2' not in tree._items
    map = [
        ('root_node1', 'val2'),
        ('root_node2_subnode1_2', '6'),
        ('root_node3_0_subnode1_subsubnode1', 'bar'),
        ('root_node3_1_subnode3', '1')
    ]
    for itm, val in map:
        tree_item = tree._items[itm]
        assert tree_item.text(1) == val

    tree._receive_data({})
    assert len(tree._items) == 1
    assert 'root' in tree._items