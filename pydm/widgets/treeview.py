import numpy as np
from qtpy import QtWidgets

from .base import PyDMWidget


class PyDMTreeView(QtWidgets.QWidget, PyDMWidget):

    def __init__(self, parent=None, init_channel=None):
        QtWidgets.QWidget.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel)
        self._items = {}
        self.setLayout(QtWidgets.QVBoxLayout())
        self.widget = QtWidgets.QTreeWidget(self)
        self.widget.setHeaderLabels(['Key', 'Value'])
        self.layout().addWidget(self.widget)
        self._items['root'] = self.widget.invisibleRootItem()
        self._visited_items = set(['root'])

    def _create_node(self, parent, name, display, value, expanded=True):
        if name not in self._items:
            widget = QtWidgets.QTreeWidgetItem(self._items[parent])
            widget.setText(0, display)
            widget.setExpanded(expanded)
            self._items[name] = widget
            try:
                self._items[parent].addChild(widget)
            except:
                pass

    def _parse_data(self, data, parent='root'):
        def parse(item, parent, index=None):
            if not isinstance(item, dict):
                self._items[parent].setText(1, str(item))
                return
            for k, v in item.items():
                name = "{}_{}".format(parent, k)
                display = k

                self._visited_items.add(name)

                self._create_node(parent, name, display, v, True)

                if isinstance(v, (dict, list)):
                    self._parse_data(v, name)
                else:
                    if name not in self._items:
                        self._create_node(parent, name, v, False)
                    else:
                        if isinstance(v, np.ndarray):
                            val = 'Array of shape: {}'.format(v.shape)
                            self._items[name].setText(1, val)
                        else:
                            self._items[name].setText(1, str(v))

        if isinstance(data, list):
            for idx, itm in enumerate(data):
                name = "{}_{}".format(parent, idx)
                display = str(idx)
                self._visited_items.add(name)
                self._create_node(parent, name, display, None, True)
                parse(itm, name, idx)
        elif isinstance(data, dict):
            return parse(data, parent)

    def _receive_data(self, data=None, introspection=None, *args, **kwargs):
        super(PyDMTreeView, self)._receive_data(data, introspection, *args,
                                                **kwargs)
        self._visited_items = set(['root'])
        self._parse_data(data)
        # Cleanup routine
        keys = set(self._items.keys())
        skipped = keys - self._visited_items
        for entry in skipped:
            item = self._items.pop(entry)
            try:
                if item.parent() is None:
                    self.widget.invisibleRootItem().removeChild(item)
                else:
                    item.parent().removeChild(item)
            except:
                # We are skipping here the case in which we deleted the parent
                # already and that will generate a RuntimeError as the
                # underlying Qt object is already dead. RIP.
                pass
