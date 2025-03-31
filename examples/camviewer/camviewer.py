# import epics
# from qtpy import uic
import functools
import weakref
from qtpy.QtCore import Slot, Signal, QPointF, QRectF
from qtpy.QtGui import QPen
from qtpy.QtWidgets import QSizePolicy
from pydm import Display
from pydm.widgets.channel import PyDMChannel
from pydm.widgets.base import widget_destroyed
from pydm.widgets.colormaps import cmap_names
from pydm.utilities import establish_widget_connections, close_widget_connections
import numpy as np
from pyqtgraph import PlotWidget, mkPen
from marker import ImageMarker
import time


class CamViewer(Display):
    # Emitted when the user changes the value.
    roi_x_signal = Signal(str)
    roi_y_signal = Signal(str)
    roi_w_signal = Signal(str)
    roi_h_signal = Signal(str)

    def __init__(self, parent=None, args=None):
        super().__init__(parent=parent, args=args)

        # Set up the list of cameras, and all the PVs
        test_dict = {
            "image": "ca://MTEST:Image",
            "max_width": "ca://MTEST:ImageWidth",
            "max_height": "ca://MTEST:ImageWidth",
            "roi_x": None,
            "roi_y": None,
            "roi_width": None,
            "roi_height": None,
        }
        # self.cameras = { "VCC": vcc_dict, "C-Iris": c_iris_dict, "Test": test_dict }
        self.cameras = {"Testing IOC Image": test_dict}
        self._channels = []
        self.imageChannel = None

        # Populate the camera combo box
        self.ui.cameraComboBox.clear()
        for camera in self.cameras:
            self.ui.cameraComboBox.addItem(camera)

        # When the camera combo box changes, disconnect from PVs, re-initialize, then reconnect.
        self.ui.cameraComboBox.currentTextChanged.connect(self.cameraChanged)

        # Set up the color map combo box.
        self.ui.colorMapComboBox.clear()
        for key, map_name in cmap_names.items():
            self.ui.colorMapComboBox.addItem(map_name, userData=key)
        self.ui.imageView.colorMap = self.ui.colorMapComboBox.currentData()
        self.ui.colorMapComboBox.currentTextChanged.connect(self.colorMapChanged)

        # Set up the color map limit sliders and line edits.
        # self._color_map_limit_sliders_need_config = True
        self.ui.colorMapMinSlider.valueChanged.connect(self.setColorMapMin)
        self.ui.colorMapMaxSlider.valueChanged.connect(self.setColorMapMax)
        self.ui.colorMapMinLineEdit.returnPressed.connect(self.colorMapMinLineEditChanged)
        self.ui.colorMapMaxLineEdit.returnPressed.connect(self.colorMapMaxLineEditChanged)

        # Set up the stuff for single-shot and average modes.
        self.ui.singleShotRadioButton.setChecked(True)
        self._average_mode_enabled = False
        self.ui.singleShotRadioButton.clicked.connect(self.enableSingleShotMode)
        self.ui.averageRadioButton.clicked.connect(self.enableAverageMode)
        self.ui.numShotsLineEdit.returnPressed.connect(self.numAverageChanged)

        # Add a plot for vertical lineouts
        self.yLineoutPlot = PlotWidget()
        self.yLineoutPlot.setMaximumWidth(80)
        self.yLineoutPlot.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.yLineoutPlot.getPlotItem().invertY()
        self.yLineoutPlot.hideAxis("bottom")
        # self.yLineoutPlot.setYLink(self.ui.imageView.getView())
        self.ui.imageGridLayout.addWidget(self.yLineoutPlot, 0, 0)
        self.yLineoutPlot.hide()
        # We do some mangling of the .ui file here and move the imageView over a cell, kind of ugly.
        self.ui.imageGridLayout.removeWidget(self.ui.imageView)
        self.ui.imageGridLayout.addWidget(self.ui.imageView, 0, 1)

        # Add a plot for the horizontal lineouts
        self.xLineoutPlot = PlotWidget()
        self.xLineoutPlot.setMaximumHeight(80)
        self.xLineoutPlot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.xLineoutPlot.hideAxis("left")
        # self.xLineoutPlot.setXLink(self.ui.imageView.getView())
        self.ui.imageGridLayout.addWidget(self.xLineoutPlot, 1, 1)
        self.xLineoutPlot.hide()

        # Update the lineout plot ranges when the image gets panned or zoomed
        self.ui.imageView.getView().sigRangeChanged.connect(self.updateLineoutRange)

        # Instantiate markers.
        self.marker_dict = {1: {}, 2: {}, 3: {}, 4: {}}
        marker_size = QPointF(20.0, 20.0)
        self.marker_dict[1]["marker"] = ImageMarker((0, 0), size=marker_size, pen=mkPen((100, 100, 255), width=5))
        self.marker_dict[1]["button"] = self.ui.marker1Button
        self.marker_dict[1]["xlineedit"] = self.ui.marker1XPosLineEdit
        self.marker_dict[1]["ylineedit"] = self.ui.marker1YPosLineEdit

        self.marker_dict[2]["marker"] = ImageMarker((0, 0), size=marker_size, pen=mkPen((255, 100, 100), width=5))
        self.marker_dict[2]["button"] = self.ui.marker2Button
        self.marker_dict[2]["xlineedit"] = self.ui.marker2XPosLineEdit
        self.marker_dict[2]["ylineedit"] = self.ui.marker2YPosLineEdit

        self.marker_dict[3]["marker"] = ImageMarker((0, 0), size=marker_size, pen=mkPen((60, 255, 60), width=5))
        self.marker_dict[3]["button"] = self.ui.marker3Button
        self.marker_dict[3]["xlineedit"] = self.ui.marker3XPosLineEdit
        self.marker_dict[3]["ylineedit"] = self.ui.marker3YPosLineEdit

        self.marker_dict[4]["marker"] = ImageMarker((0, 0), size=marker_size, pen=mkPen((255, 60, 255), width=5))
        self.marker_dict[4]["button"] = self.ui.marker4Button
        self.marker_dict[4]["xlineedit"] = self.ui.marker4XPosLineEdit
        self.marker_dict[4]["ylineedit"] = self.ui.marker4YPosLineEdit
        # Disable auto-ranging the image (it feels strange when the zoom changes as you move markers around.)
        self.ui.imageView.getView().getViewBox().disableAutoRange()
        for d in self.marker_dict:
            marker = self.marker_dict[d]["marker"]
            marker.setZValue(20)
            marker.hide()
            marker.sigRegionChanged.connect(self.markerMoved)
            self.ui.imageView.getView().getViewBox().addItem(marker)
            self.marker_dict[d]["button"].toggled.connect(self.enableMarker)
            curvepen = QPen(marker.pen)
            curvepen.setWidth(1)
            self.marker_dict[d]["xcurve"] = self.xLineoutPlot.plot(pen=curvepen)
            self.marker_dict[d]["ycurve"] = self.yLineoutPlot.plot(pen=curvepen)
            self.marker_dict[d]["xlineedit"].returnPressed.connect(self.markerPositionLineEditChanged)
            self.marker_dict[d]["ylineedit"].returnPressed.connect(self.markerPositionLineEditChanged)

        # Set up zoom buttons
        self.ui.zoomInButton.clicked.connect(self.zoomIn)
        self.ui.zoomOutButton.clicked.connect(self.zoomOut)
        self.ui.zoomToActualSizeButton.clicked.connect(self.zoomToActualSize)

        # Set up ROI buttons
        self.ui.setROIButton.clicked.connect(self.setROI)
        self.ui.resetROIButton.clicked.connect(self.resetROI)

        self.destroyed.connect(functools.partial(widget_destroyed, self.channels, weakref.ref(self)))

    @Slot()
    def zoomIn(self):
        self.ui.imageView.getView().getViewBox().scaleBy((0.5, 0.5))

    @Slot()
    def zoomOut(self):
        self.ui.imageView.getView().getViewBox().scaleBy((2.0, 2.0))

    @Slot()
    def zoomToActualSize(self):
        if len(self.image_data) == 0:
            return
        self.ui.imageView.getView().setRange(
            xRange=(0, self.image_data.shape[0]), yRange=(0, self.image_data.shape[1]), padding=0.0
        )

    def disable_all_markers(self):
        for d in self.marker_dict:
            self.marker_dict[d]["button"].setChecked(False)
            self.marker_dict[d]["marker"].setPos((0, 0))

    @Slot(bool)
    def enableMarker(self, checked):
        any_markers_visible = False
        for d in self.marker_dict:
            marker = self.marker_dict[d]["marker"]
            button = self.marker_dict[d]["button"]
            any_markers_visible = any_markers_visible or button.isChecked()
            marker.setVisible(button.isChecked())
            self.markerMoved(d)
            self.marker_dict[d]["xcurve"].setVisible(button.isChecked())
            self.marker_dict[d]["ycurve"].setVisible(button.isChecked())
            self.marker_dict[d]["xlineedit"].setEnabled(button.isChecked())
            self.marker_dict[d]["ylineedit"].setEnabled(button.isChecked())
        if any_markers_visible:
            self.xLineoutPlot.show()
            self.yLineoutPlot.show()
        else:
            self.xLineoutPlot.hide()
            self.yLineoutPlot.hide()

    @Slot()
    def markerPositionLineEditChanged(self):
        for d in self.marker_dict:
            marker = self.marker_dict[d]["marker"]
            x_line_edit = self.marker_dict[d]["xlineedit"]
            y_line_edit = self.marker_dict[d]["ylineedit"]
            try:
                new_x = int(x_line_edit.text())
                new_y = int(y_line_edit.text())
                if new_x <= marker.maxBounds.width() and new_y <= marker.maxBounds.height():
                    marker.setPos((new_x, new_y))
            except Exception:
                pass
            coords = marker.getPixelCoords()
            x_line_edit.setText(str(coords[0]))
            y_line_edit.setText(str(coords[1]))

    @Slot(object)
    def markerMoved(self, marker):
        self.updateLineouts()
        for marker_index in self.marker_dict:
            marker = self.marker_dict[marker_index]["marker"]
            x_line_edit = self.marker_dict[marker_index]["xlineedit"]
            y_line_edit = self.marker_dict[marker_index]["ylineedit"]
            coords = marker.getPixelCoords()
            x_line_edit.setText(str(coords[0]))
            y_line_edit.setText(str(coords[1]))

    @Slot(object, object)
    def updateLineoutRange(self, view, new_ranges):
        self.ui.xLineoutPlot.setRange(xRange=new_ranges[0], padding=0.0)
        self.ui.yLineoutPlot.setRange(yRange=new_ranges[1], padding=0.0)

    def updateLineouts(self):
        for marker_index in self.marker_dict:
            marker = self.marker_dict[marker_index]["marker"]
            xcurve = self.marker_dict[marker_index]["xcurve"]
            ycurve = self.marker_dict[marker_index]["ycurve"]
            if marker.isVisible():
                result, coords = marker.getArrayRegion(self.image_data, self.ui.imageView.getImageItem())
                xcurve.setData(y=result[0], x=np.arange(len(result[0])))
                ycurve.setData(y=np.arange(len(result[1])), x=result[1])

    @Slot()
    def enableSingleShotMode(self):
        self._average_mode_enabled = False
        self._average_buffer = np.ndarray(0)

    @Slot()
    def enableAverageMode(self):
        self._average_mode_enabled = True

    @Slot(str)
    def cameraChanged(self, new_camera):
        new_camera = str(new_camera)
        if self.imageChannel == self.cameras[new_camera]["image"]:
            return
        close_widget_connections(self)
        self.disable_all_markers()
        self.initializeCamera(new_camera)

    def initializeCamera(self, new_camera):
        new_camera = str(new_camera)
        self._color_map_limit_sliders_need_config = True
        self.times = np.zeros(10)
        self.old_timestamp = 0
        self.image_width = 0  # current width (width of ROI)
        self.image_max_width = 0  # full width.  Only used to reset ROI to full.
        self.image_max_height = 0  # full height.  Only used to reset ROI to full.
        self.image_data = np.zeros(0)
        self._average_counter = 0
        self._average_buffer = np.ndarray(0)
        self._needs_auto_range = True
        self.imageChannel = self.cameras[new_camera]["image"]
        self.widthChannel = self.cameras[new_camera]["roi_width"] or self.cameras[new_camera]["max_width"]
        self.maxWidthChannel = self.cameras[new_camera]["max_width"]
        self.maxHeightChannel = self.cameras[new_camera]["max_height"]
        self.roiXChannel = self.cameras[new_camera]["roi_x"]
        self.roiYChannel = self.cameras[new_camera]["roi_y"]
        self.roiWidthChannel = self.cameras[new_camera]["roi_width"]
        self.roiHeightChannel = self.cameras[new_camera]["roi_height"]

        self._channels = [
            PyDMChannel(
                address=self.imageChannel,
                connection_slot=self.connectionStateChanged,
                value_slot=self.receiveImageWaveform,
                severity_slot=self.alarmSeverityChanged,
            ),
            PyDMChannel(address=self.widthChannel, value_slot=self.receiveImageWidth),
            PyDMChannel(address=self.maxWidthChannel, value_slot=self.receiveMaxWidth),
            PyDMChannel(address=self.maxHeightChannel, value_slot=self.receiveMaxHeight),
        ]
        if self.roiXChannel and self.roiYChannel and self.roiWidthChannel and self.roiHeightChannel:
            self._channels.extend(
                [
                    PyDMChannel(
                        address=self.roiXChannel,
                        value_slot=self.receiveRoiX,
                        value_signal=self.roi_x_signal,
                        write_access_slot=self.roiWriteAccessChanged,
                    ),
                    PyDMChannel(address=self.roiYChannel, value_slot=self.receiveRoiY, value_signal=self.roi_y_signal),
                    PyDMChannel(
                        address=self.roiWidthChannel, value_slot=self.receiveRoiWidth, value_signal=self.roi_w_signal
                    ),
                    PyDMChannel(
                        address=self.roiHeightChannel, value_slot=self.receiveRoiHeight, value_signal=self.roi_h_signal
                    ),
                ]
            )
            self.ui.roiXLineEdit.setEnabled(True)
            self.ui.roiYLineEdit.setEnabled(True)
            self.ui.roiWLineEdit.setEnabled(True)
            self.ui.roiHLineEdit.setEnabled(True)
        else:
            self.ui.roiXLineEdit.clear()
            self.ui.roiXLineEdit.setEnabled(False)
            self.ui.roiYLineEdit.clear()
            self.ui.roiYLineEdit.setEnabled(False)
            self.ui.roiWLineEdit.clear()
            self.ui.roiWLineEdit.setEnabled(False)
            self.ui.roiHLineEdit.clear()
            self.ui.roiHLineEdit.setEnabled(False)
        establish_widget_connections(self)

    @Slot()
    def setROI(self):
        self.roi_x_signal.emit(self.ui.roiXLineEdit.text())
        self.roi_y_signal.emit(self.ui.roiYLineEdit.text())
        self.roi_w_signal.emit(self.ui.roiWLineEdit.text())
        self.roi_h_signal.emit(self.ui.roiHLineEdit.text())

    @Slot()
    def resetROI(self):
        self.roi_x_signal.emit(str(0))
        self.roi_y_signal.emit(str(0))
        self.roi_w_signal.emit(str(self.image_max_width))
        self.roi_h_signal.emit(str(self.image_max_height))

    @Slot(str)
    def colorMapChanged(self, _):
        self.ui.imageView.colorMap = self.ui.colorMapComboBox.currentData()

    def configureColorMapLimitSliders(self, max_int):
        self.ui.colorMapMinSlider.setMaximum(max_int)
        self.ui.colorMapMaxSlider.setMaximum(max_int)
        self.ui.colorMapMaxSlider.setValue(max_int)
        self.ui.colorMapMinSlider.setValue(0)
        self.setColorMapMin(0)
        self.setColorMapMax(max_int)
        self._color_map_limit_sliders_need_config = False

    @Slot()
    def colorMapMinLineEditChanged(self):
        try:
            new_min = int(self.ui.colorMapMinLineEdit.text())
        except Exception:
            self.ui.colorMapMinLineEdit.setText(str(self.ui.colorMapMinSlider.value()))
            return
        if new_min < 0:
            new_min = 0
        if new_min > self.ui.colorMapMinSlider.maximum():
            new_min = self.ui.colorMapMinSlider.maximum()
        self.ui.colorMapMinSlider.setValue(new_min)

    @Slot(int)
    def setColorMapMin(self, new_min):
        if new_min > self.ui.colorMapMaxSlider.value():
            self.ui.colorMapMaxSlider.setValue(new_min)
            self.ui.colorMapMaxLineEdit.setText(str(new_min))
        self.ui.colorMapMinLineEdit.setText(str(new_min))
        self.ui.imageView.setColorMapLimits(new_min, self.ui.colorMapMaxSlider.value())

    @Slot()
    def colorMapMaxLineEditChanged(self):
        try:
            new_max = int(self.ui.colorMapMaxLineEdit.text())
        except Exception:
            self.ui.colorMapMaxLineEdit.setText(str(self.ui.colorMapMaxSlider.value()))
            return
        if new_max < 0:
            new_max = 0
        if new_max > self.ui.colorMapMaxSlider.maximum():
            new_max = self.ui.colorMapMaxSlider.maximum()
        self.ui.colorMapMaxSlider.setValue(new_max)

    @Slot(int)
    def setColorMapMax(self, new_max):
        if new_max < self.ui.colorMapMinSlider.value():
            self.ui.colorMapMinSlider.setValue(new_max)
            self.ui.colorMapMinLineEdit.setText(str(new_max))
        self.ui.colorMapMaxLineEdit.setText(str(new_max))
        self.ui.imageView.setColorMapLimits(self.ui.colorMapMinSlider.value(), new_max)

    def createAverageBuffer(self, size, type, initial_val=[]):
        num_shots = 1
        try:
            num_shots = int(self.ui.numShotsLineEdit.text())
        except Exception:
            self.ui.numShotsLineEdit.setText(str(num_shots))
        if num_shots < 1:
            num_shots = 1
            self.ui.numShotsLineEdit.setText(str(num_shots))
        if num_shots > 200:
            num_shots = 200
            self.ui.numShotsLineEdit.setText(str(num_shots))
        if len(initial_val) > 0:
            return np.full((num_shots, size), initial_val, dtype=type)
        else:
            return np.zeros(shape=(num_shots, size), dtype=type)

    @Slot()
    def numAverageChanged(self):
        self._average_buffer = np.zeros(0)

    @Slot(np.ndarray)
    def receiveImageWaveform(self, new_waveform):
        if not self.image_width:
            return

        # Calculate the average rate
        new_timestamp = time.time()
        if not (self.old_timestamp == 0):
            delta = new_timestamp - self.old_timestamp
            self.times = np.roll(self.times, 1)
            self.times[0] = delta
            avg_delta = np.mean(self.times)
            self.ui.dataRateLabel.setText("{:.1f} Hz".format((1.0 / avg_delta)))
            self.ui.displayRateLabel.setText("{:.1f} Hz".format((1.0 / avg_delta)))
        self.old_timestamp = new_timestamp

        # If this is the first image, set up the color map slider limits
        if self._color_map_limit_sliders_need_config:
            max_int = np.iinfo(new_waveform.dtype).max
            self.configureColorMapLimitSliders(max_int)

        # If we are in average mode, add this image to the circular averaging buffer, otherwise just display it.
        if self._average_mode_enabled:
            if len(self._average_buffer) == 0:
                self._average_buffer = self.createAverageBuffer(len(new_waveform), new_waveform.dtype, new_waveform)
                self._average_counter = 0
            self._average_counter = (self._average_counter + 1) % len(self._average_buffer)
            # self._average_buffer = np.roll(self._average_buffer, 1, axis=0)
            self._average_buffer[self._average_counter] = new_waveform
            mean = np.mean(self._average_buffer, axis=0).astype(new_waveform.dtype)
            self.image_data = mean.reshape((int(self.image_width), -1), order="F")
        else:
            self.image_data = new_waveform.reshape((int(self.image_width), -1), order="F")
        self.setMarkerBounds()
        self.updateLineouts()
        self.ui.imageView.image_value_changed(self.image_data)
        self.calculateStats()
        if self._needs_auto_range:
            self.ui.imageView.getView().autoRange(padding=0.0)
            self.ui.imageView.getView().viewRange()
            self._needs_auto_range = False

    def calculateStats(self):
        # Full image stats
        mean = np.mean(self.image_data)
        std = np.std(self.image_data)
        width = self.image_data.shape[0]
        height = self.image_data.shape[1]
        min_val = np.min(self.image_data)
        max_val = np.max(self.image_data)
        self.ui.imageStatsLabel.setText(
            "Mean: {0:.2f}, Std: {1:.2f}, Min: {2}, Max: {3}, Width: {4}, Height: {5}".format(
                mean, std, min_val, max_val, width, height
            )
        )
        # Current view stats
        current_range = self.ui.imageView.getView().viewRange()
        view_x_min = int(max(0, current_range[0][0]))
        view_x_max = int(min(self.image_data.shape[0], current_range[0][1]))
        view_y_min = int(max(0, current_range[1][0]))
        view_y_max = int(min(self.image_data.shape[1], current_range[1][1]))
        view_slice = self.image_data[view_x_min:view_x_max, view_y_min:view_y_max]
        mean = np.mean(view_slice)
        std = np.std(view_slice)
        width = view_slice.shape[0]
        height = view_slice.shape[1]
        min_val = np.min(view_slice)
        max_val = np.max(view_slice)
        self.ui.viewStatsLabel.setText(
            "Mean: {0:.2f}, Std: {1:.2f}, Min: {2}, Max: {3}, Width: {4}, Height: {5}".format(
                mean, std, min_val, max_val, width, height
            )
        )

    def setMarkerBounds(self):
        for marker_index in self.marker_dict:
            marker = self.marker_dict[marker_index]["marker"]
            marker.maxBounds = QRectF(
                0, 0, self.image_data.shape[0] + marker.size()[0] - 1, self.image_data.shape[1] + marker.size()[1] - 1
            )

    @Slot(int)
    def receiveImageWidth(self, new_width):
        self.image_width = new_width
        self.ui.imageView.image_width_changed(self.image_width)

    @Slot(int)
    def receiveMaxWidth(self, new_max_width):
        self.image_max_width = new_max_width

    @Slot(int)
    def receiveMaxHeight(self, new_max_height):
        self.image_max_height = new_max_height

    @Slot(int)
    def receiveRoiX(self, new_roi_x):
        self.ui.roiXLineEdit.setText(str(new_roi_x))

    @Slot(int)
    def receiveRoiY(self, new_roi_y):
        self.ui.roiYLineEdit.setText(str(new_roi_y))

    @Slot(int)
    def receiveRoiWidth(self, new_roi_w):
        self.ui.roiWLineEdit.setText(str(new_roi_w))

    @Slot(int)
    def receiveRoiHeight(self, new_roi_h):
        self.ui.roiHLineEdit.setText(str(new_roi_h))

    # -2 to +2, -2 is LOLO, -1 is LOW, 0 is OK, etc.
    @Slot(int)
    def alarmStatusChanged(self, new_alarm_state):
        pass

    # 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR, 3 = INVALID
    @Slot(int)
    def alarmSeverityChanged(self, new_alarm_severity):
        pass

    @Slot(bool)
    def roiWriteAccessChanged(self, can_write_roi):
        self.ui.setROIButton.setEnabled(can_write_roi)
        self.ui.resetROIButton.setEnabled(can_write_roi)
        self.ui.roiXLineEdit.setReadOnly(not can_write_roi)
        self.ui.roiYLineEdit.setReadOnly(not can_write_roi)
        self.ui.roiWLineEdit.setReadOnly(not can_write_roi)
        self.ui.roiHLineEdit.setReadOnly(not can_write_roi)

    # false = disconnected, true = connected
    @Slot(bool)
    def connectionStateChanged(self, connected):
        if connected:
            self.ui.imageView.redraw_timer.start()
        else:
            self.ui.imageView.redraw_timer.stop()
        self.ui.connectedLabel.setText({True: "Yes", False: "No"}[connected])

    def ui_filename(self):
        return "camviewer.ui"

    def channels(self):
        return self._channels


intelclass = CamViewer
