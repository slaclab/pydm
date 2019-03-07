from qtpy import QtWidgets

from .base import PyDMWidget


class PyDMTreeView(QtWidgets.QWidget, PyDMWidget):

    def __init__(self, parent, init_channel=None, data={}):
        QtWidgets.QWidget.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel)
        self._items = {}
        self.setLayout(QtWidgets.QVBoxLayout())
        self.widget = QtWidgets.QTreeWidget(self)
        self.widget.setHeaderLabels(['Key', 'Value'])
        self.layout().addWidget(self.widget)
        self._items['root'] = self.widget
        self._visited_items = set(['root'])

    def _create_node(self, parent, name, value, expanded=True):
        if name not in self._items:
            widget = QtWidgets.QTreeWidgetItem(self._items[parent])
            widget.setText(0, name.split('_')[-1])
            widget.setExpanded(expanded)
            self._items[name] = widget
            try:
                self._items[parent].addChild(widget)
            except:
                pass
            if isinstance(value, list) and not isinstance(value[0], dict):
                widget.setText(1, str(value))

    def _parse_data(self, data, parent='root'):
        def parse(item, parent, index=None):
            if not isinstance(item, dict):
                return
            for k, v in item.items():
                if index is not None:
                    name = "{}_{}_{}".format(parent, index, k)
                else:
                    name = "{}_{}".format(parent, k)

                self._visited_items.add(name)

                self._create_node(parent, name, v, True)

                if isinstance(v, (dict, list)):
                    self._parse_data(v, name)
                else:
                    if name not in self._items:
                        self._create_node(parent, name, v, False)
                    else:
                        self._items[name].setText(1, str(v))

        if isinstance(data, list):
            for idx, itm in enumerate(data):
                name = "{}_{}".format(parent, idx)
                self._visited_items.add(name)
                self._create_node(parent, name, None, True)
                parse(itm, name, idx)
        elif isinstance(data, dict):
            return parse(data, parent)

    def _receive_data(self, data=None, introspection=None, *args, **kwargs):
        self._visited_items = set(['root'])
        self._parse_data(data)
        # Cleanup routine
        keys = set(self._items.keys())
        skipped = keys - self._visited_items
        for entry in skipped:
            item = self._items.pop(entry)
            try:
                item.parent().removeChild(item)
            except:
                # We are skipping here the case in which we deleted the parent
                # already and that will generate a RuntimeError as the
                # underlying Qt object is already dead. RIP.
                pass
