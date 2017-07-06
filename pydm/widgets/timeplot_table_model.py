from PyQt4.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from operator import itemgetter

from timeplot import TimePlotCurveItem
from .. import utilities

class PyDMTimePlotCurvesModel(QAbstractTableModel):
	def __init__(self, plot, parent=None):
		super(PyDMTimePlotCurvesModel, self).__init__(parent=parent)
		self._plot = plot
		self._column_names = ("Channel", "Label", "Color")

	@property
	def plot(self):
		return self._plot

	@plot.setter
	def plot(self, new_plot):
		self.beginResetModel()
		self._plot = new_plot
		self.endResetModel()

	#QAbstractItemModel Implementation
	def clear(self):
		self.plot.clearCurves()

	def flags(self, index):
		f = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
		return f

	def rowCount(self, parent=None):
		if parent is not None and parent.isValid():
			return 0
		return len(self.plot.curves())

	def columnCount(self, parent=None):
		return len(self._column_names)

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return QVariant()
		if index.row() >= self.rowCount():
			return QVariant()
		if index.column() >= self.columnCount():
			return QVariant()
    column_name = self._column_names[index.column()]
    curve = self.plot.curves.values()[index.row()]
		if role == Qt.DisplayRole:
      if column_name == "Channel":
        return str(curve.channel.address)
      elif column_name == "Label":
        return str(curve.curve_name)
      elif column_name == "Color":
        return curve.color_string
    #elif role == Qt.DecorationRole and column_name == "Color":
    #  return curve.color
    elif role == Qt.BackgroundRole and column_name == "Color":
      return QBrush(curve.color)
		else:
			return QVariant()

	def setData(self, index, value, role=Qt.EditRole):
		if role != Qt.EditRole:
			return False
		if not index.isValid():
			return False
		if index.row() >= self.rowCount():
			return False
		if index.column() >= self.columnCount():
			return False
    column_name = self._column_names[index.column()]
    curve = self.plot.curves.values()[index.row()]
    if column_name == "Channel":
      curve.address = str(value)
    elif column_name == "Label":
      curve.curve_name = str(value)
    elif column_name == "Color":
      curve.color_string = str(value)
		self.dataChanged.emit(index, index)
		return True

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role != Qt.DisplayRole:
			return super(PythonTableModel, self).headerData(section, orientation, role)
		if orientation == Qt.Horizontal and section < self.columnCount():
			return str(self._column_names[section])
		elif orientation == Qt.Vertical and section < self.rowCount():
			return section

	#def sort(self, col, order=Qt.AscendingOrder):
  #	self.layoutAboutToBeChanged.emit()
	#	sort_reversed = (order == Qt.AscendingOrder)
	#	self._list.sort(key=itemgetter(col), reverse=sort_reversed)
	#	self.layoutChanged.emit()
	#End QAbstractItemModel implementation.

	def append(self, value):
		self.beginInsertRows(QModelIndex(), len(self._list), len(self._list))
		self._plot..append(value)
		self.endInsertRows()

	def remove(self, item):
		index = None
		try:
			index = self._list.index(item)
		except ValueError:
			raise ValueError("list.remove(x): x not in list")
		del self[index]

	def count(self, item):
		return self._list.count(item)

	def reverse(self):
		self.layoutAboutToBeChanged.emit()
		self._list.reverse()
		self.layoutChanged.emit()