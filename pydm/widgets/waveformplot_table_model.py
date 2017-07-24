from ..PyQt.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from ..PyQt.QtGui import QBrush, QColor
from operator import itemgetter
from .. import utilities

class PyDMWaveformPlotCurvesModel(QAbstractTableModel):
	def __init__(self, plot, parent=None):
		super(PyDMWaveformPlotCurvesModel, self).__init__(parent=parent)
		self._plot = plot
		self._column_names = ("Y Channel", "X Channel", "Label", "Color")

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
		return len(self.plot._curves)

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
		curve = self.plot._curves[index.row()]
		if role == Qt.DisplayRole or role == Qt.EditRole:
			if column_name == "Y Channel":
				if curve.y_address is None:
					return QVariant()
				return str(curve.y_address)
			elif column_name == "X Channel":
				if curve.x_address is None:
					return QVariant()
				return str(curve.x_address)
			elif column_name == "Label":
				if curve.name() is None:
					return QVariant()
				return str(curve.name())
			elif column_name == "Color":
				return curve.color_string
		#elif role == Qt.DecorationRole and column_name == "Color":
		#	 return curve.color
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
		curve = self.plot._curves[index.row()]
		if isinstance(value, QVariant):
			value = value.toString()
		if column_name == "Y Channel":
			curve.y_address = str(value)
		elif column_name == "X Channel":
			curve.x_address = str(value)
		elif column_name == "Label":
			curve.setData(name=str(value))
		elif column_name == "Color":
			curve.color_string = str(value)
		self.dataChanged.emit(index, index)
		return True

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role != Qt.DisplayRole:
			return super(PyDMWaveformPlotCurvesModel, self).headerData(section, orientation, role)
		if orientation == Qt.Horizontal and section < self.columnCount():
			return str(self._column_names[section])
		elif orientation == Qt.Vertical and section < self.rowCount():
			return section
	#End QAbstractItemModel implementation.

	def append(self, y_address=None, x_address=None, name=None, color=None):
		self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
		self._plot.addChannel(y_address, x_address, name, color)
		self.endInsertRows()

	def removeAtIndex(self, index):
		self.beginRemoveRows(QModelIndex(), index.row(), index.row())
		self._plot.removeChannelAtIndex(index.row())
		self.endRemoveRows()