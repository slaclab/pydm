"""
Test panel for the Tango data plugin, using the TangoTest device server.

Run with::

    export TANGO_HOST=localhost:10000
    pydm examples/tango/tango_test_panel.py

or for another TangoTest instance::

    pydm -m "DEVICE=sys/tg_test/2" examples/tango/tango_test_panel.py

TangoTest does not configure change events, so the plugin polls the attributes
(see PYDM_TANGO_POLL_PERIOD).
"""

from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor
from qtpy.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pydm import Display
from pydm.widgets import (
    PyDMByteIndicator,
    PyDMCheckbox,
    PyDMDrawingCircle,
    PyDMEnumButton,
    PyDMEnumComboBox,
    PyDMFrame,
    PyDMImageView,
    PyDMLabel,
    PyDMLineEdit,
    PyDMMultiStateIndicator,
    PyDMPushButton,
    PyDMScaleIndicator,
    PyDMScatterPlot,
    PyDMSlider,
    PyDMSpinbox,
    PyDMTimePlot,
    PyDMWaveformPlot,
    PyDMWaveformTable,
)
from pydm.widgets.analog_indicator import PyDMAnalogIndicator

# The usual Tango colors for DevState, indexed by the state value
STATE_COLORS = [
    (0, 255, 0),  # ON
    (255, 255, 255),  # OFF
    (255, 255, 255),  # CLOSE
    (0, 255, 0),  # OPEN
    (255, 255, 255),  # INSERT
    (0, 255, 0),  # EXTRACT
    (128, 160, 255),  # MOVING
    (255, 255, 0),  # STANDBY
    (255, 0, 0),  # FAULT
    (204, 204, 122),  # INIT
    (0, 125, 0),  # RUNNING
    (255, 140, 0),  # ALARM
    (255, 0, 255),  # DISABLE
    (155, 155, 155),  # UNKNOWN
]


class TangoTestPanel(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        self.device = self.macros().get("DEVICE", "sys/tg_test/1")
        self.setWindowTitle("TangoTest panel - {}".format(self.device))
        self.setup_ui()

    def ui_filename(self):
        return None

    def ui_filepath(self):
        return None

    def ch(self, attribute):
        return "tango://{}/{}".format(self.device, attribute)

    def setup_ui(self):
        tabs = QTabWidget()
        tabs.addTab(self.read_tab(), "Scalars (read)")
        tabs.addTab(self.write_tab(), "Scalars (write)")
        tabs.addTab(self.indicator_tab(), "Indicators")
        tabs.addTab(self.spectrum_tab(), "Spectra")
        tabs.addTab(self.plot_tab(), "Time && scatter plots")
        tabs.addTab(self.image_tab(), "Images")

        header = QHBoxLayout()
        state = PyDMLabel(init_channel=self.ch("State"))
        state.alarmSensitiveBorder = True
        header.addWidget(QLabel("<b>{}</b>".format(self.device)))
        header.addWidget(state)
        header.addWidget(PyDMLabel(init_channel=self.ch("Status")), 1)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(tabs)
        self.resize(1000, 750)

    @staticmethod
    def grid(rows, headers):
        """Build a grid layout from rows of widgets, with the attribute name in the first column."""
        widget = QWidget()
        grid = QGridLayout(widget)
        for col, text in enumerate(headers):
            grid.addWidget(QLabel("<b>{}</b>".format(text)), 0, col)
        for row, (name, *widgets) in enumerate(rows, start=1):
            grid.addWidget(QLabel(name), row, 0)
            for col, w in enumerate(widgets, start=1):
                grid.addWidget(w, row, col)
        grid.setColumnStretch(len(headers) - 1, 1)
        grid.setRowStretch(len(rows) + 1, 1)
        return widget

    def label(self, attribute):
        label = PyDMLabel(init_channel=self.ch(attribute))
        label.showUnits = True
        label.alarmSensitiveBorder = True
        return label

    def read_tab(self):
        attributes = [
            ("double_scalar", "DevDouble"),
            ("float_scalar", "DevFloat"),
            ("long_scalar", "DevLong"),
            ("long64_scalar", "DevLong64"),
            ("short_scalar_ro", "DevShort, read only"),
            ("ushort_scalar", "DevUShort"),
            ("ulong_scalar", "DevULong"),
            ("ulong64_scalar", "DevULong64"),
            ("uchar_scalar", "DevUChar"),
            ("boolean_scalar", "DevBoolean, shown with its enum strings"),
            ("enum_scalar", "DevEnum, shown with its labels"),
            ("string_scalar", "DevString"),
            ("State", "DevState"),
            ("Status", "DevString"),
            ("throw_exception", "always fails to read: disconnected"),
            ("no_value", "never has a value: disconnected"),
        ]
        rows = [(name, self.label(name), QLabel(description)) for name, description in attributes]
        return self.grid(rows, ["Attribute", "PyDMLabel", "Remark"])

    def write_tab(self):
        def spinbox(attribute, precision=None):
            spinbox = PyDMSpinbox(init_channel=self.ch(attribute))
            spinbox.showStepExponent = False
            # TangoTest does not define min_value/max_value, so the spinbox needs its own limits
            spinbox.userDefinedLimits = True
            spinbox.userMinimum = -1e6
            spinbox.userMaximum = 1e6
            if precision is not None:
                spinbox.precisionFromPV = False
                spinbox.precision = precision
            return spinbox

        slider = PyDMSlider(init_channel=self.ch("short_scalar"))
        slider.userDefinedLimits = True
        slider.userMinimum = 0
        slider.userMaximum = 255
        slider.num_steps = 256

        enum_button = PyDMEnumButton(init_channel=self.ch("enum_scalar"))
        enum_button.orientation = Qt.Horizontal

        increment = PyDMPushButton(label="+1", pressValue=1, relative=True, init_channel=self.ch("long_scalar_w"))
        reset = PyDMPushButton(label="Reset to 0", pressValue=0, init_channel=self.ch("long_scalar_w"))
        buttons = QWidget()
        button_layout = QHBoxLayout(buttons)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(increment)
        button_layout.addWidget(reset)
        button_layout.addStretch()

        setpoints = [
            ("double_scalar", PyDMLineEdit(init_channel=self.ch("double_scalar")), "PyDMLineEdit"),
            ("double_scalar_w", PyDMLineEdit(init_channel=self.ch("double_scalar_w")), "PyDMLineEdit, write only"),
            ("ampli", spinbox("ampli"), "PyDMSpinbox, amplitude of 'wave'"),
            ("long_scalar", spinbox("long_scalar", 0), "PyDMSpinbox"),
            ("short_scalar", slider, "PyDMSlider"),
            ("long_scalar_w", buttons, "PyDMPushButton (relative / absolute)"),
            ("string_scalar", PyDMLineEdit(init_channel=self.ch("string_scalar")), "PyDMLineEdit"),
            ("boolean_scalar", PyDMCheckbox(init_channel=self.ch("boolean_scalar")), "PyDMCheckbox"),
            ("enum_scalar", PyDMEnumComboBox(init_channel=self.ch("enum_scalar")), "PyDMEnumComboBox"),
            ("enum_scalar", enum_button, "PyDMEnumButton"),
        ]
        rows = [(name, self.label(name), setpoint, QLabel(remark)) for name, setpoint, remark in setpoints]
        return self.grid(rows, ["Attribute", "Readback", "Setpoint", "Widget"])

    def indicator_tab(self):
        scale = PyDMScaleIndicator(init_channel=self.ch("double_scalar"))
        scale.limitsFromChannel = False
        scale.userLowerLimit = 0
        scale.userUpperLimit = 300
        scale.showValue = True

        analog = PyDMAnalogIndicator(init_channel=self.ch("short_scalar_ro"))
        analog.limitsFromChannel = False
        analog.userLowerLimit = 0
        analog.userUpperLimit = 255
        analog.minorAlarmFromChannel = False
        analog.majorAlarmFromChannel = False
        analog.userLowerMinorAlarm = 50
        analog.userUpperMinorAlarm = 200
        analog.userLowerMajorAlarm = 20
        analog.userUpperMajorAlarm = 230

        byte = PyDMByteIndicator(init_channel=self.ch("uchar_scalar"))
        byte.numBits = 8
        byte.orientation = Qt.Horizontal
        byte.circles = True

        long_bits = PyDMByteIndicator(init_channel=self.ch("long_scalar"))
        long_bits.numBits = 8
        long_bits.orientation = Qt.Horizontal

        state = PyDMMultiStateIndicator(init_channel=self.ch("State"))
        state.setMinimumSize(40, 40)
        for index, rgb in enumerate(STATE_COLORS):
            setattr(state, "state{}Color".format(index), QColor(*rgb))

        def circle(attribute):
            # The drawing changes color with the alarm severity and connection state. The brush is set
            # before the channel, so that it is taken as the color for the 'no alarm' state.
            drawing = PyDMDrawingCircle()
            drawing.brush = QBrush(QColor(0, 200, 0))
            drawing.alarmSensitiveContent = True
            drawing.channel = self.ch(attribute)
            drawing.setFixedSize(40, 40)
            return drawing

        def frame(attribute):
            frame = PyDMFrame(init_channel=self.ch(attribute))
            frame.alarmSensitiveBorder = True
            frame.disableOnDisconnect = True
            frame.setMinimumHeight(40)
            layout = QHBoxLayout(frame)
            layout.addWidget(QLabel("Contents of a PyDMFrame"))
            return frame

        rows = [
            ("double_scalar", scale, QLabel("PyDMScaleIndicator")),
            ("short_scalar_ro", analog, QLabel("PyDMAnalogIndicator, with alarm regions set in the widget")),
            ("uchar_scalar", byte, QLabel("PyDMByteIndicator")),
            ("long_scalar", long_bits, QLabel("PyDMByteIndicator, lowest 8 bits")),
            ("State", state, QLabel("PyDMMultiStateIndicator, with Tango state colors")),
            ("double_scalar", circle("double_scalar"), QLabel("PyDMDrawingCircle, alarm sensitive")),
            ("throw_exception", circle("throw_exception"), QLabel("PyDMDrawingCircle, disconnected")),
            ("double_scalar", frame("double_scalar"), QLabel("PyDMFrame, connected")),
            ("throw_exception", frame("throw_exception"), QLabel("PyDMFrame, disconnected: contents disabled")),
        ]
        return self.grid(rows, ["Attribute", "Widget", "Remark"])

    def spectrum_tab(self):
        wave = PyDMWaveformPlot()
        wave.addChannel(y_channel=self.ch("wave"), name="wave", color="cyan")
        wave.setShowLegend(True)

        bars = PyDMWaveformPlot()
        bars.addChannel(
            y_channel=self.ch("double_spectrum_ro"), name="double_spectrum_ro", color="orange", plot_style="Bar"
        )
        bars.curveAtIndex(0).bar_graph_item.setOpts(pen=None)
        bars.setShowLegend(True)

        numbers = PyDMWaveformTable(init_channel=self.ch("double_spectrum_ro"))
        numbers.columnHeaderLabels = ["double_spectrum_ro"]
        strings = PyDMWaveformTable(init_channel=self.ch("string_spectrum_ro"))
        strings.columnHeaderLabels = ["string_spectrum_ro"]
        for table in (numbers, strings):
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        tables = QHBoxLayout()
        tables.addWidget(numbers)
        tables.addWidget(strings)

        widget = QWidget()
        layout = QGridLayout(widget)
        layout.addWidget(self.group("PyDMWaveformPlot: wave (scale it with 'ampli')", wave), 0, 0)
        layout.addWidget(self.group("PyDMWaveformPlot (bars): double_spectrum_ro", bars), 0, 1)
        layout.addWidget(self.group("PyDMWaveformTable", tables), 1, 0, 1, 2)
        return widget

    def plot_tab(self):
        time_plot = PyDMTimePlot()
        time_plot.timeSpan = 120
        time_plot.addYChannel(y_channel=self.ch("double_scalar"), name="double_scalar", color="cyan")
        time_plot.addYChannel(y_channel=self.ch("short_scalar_ro"), name="short_scalar_ro", color="orange")
        time_plot.addYChannel(y_channel=self.ch("long_scalar"), name="long_scalar", color="lime")
        time_plot.setShowLegend(True)

        scatter = PyDMScatterPlot()
        scatter.addChannel(
            y_channel=self.ch("short_scalar_ro"),
            x_channel=self.ch("double_scalar"),
            name="short_scalar_ro vs. double_scalar",
            color="orange",
            symbol="o",
            lineStyle=Qt.NoPen,
            buffer_size=200,
        )
        scatter.setShowLegend(True)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(self.group("PyDMTimePlot", time_plot))
        layout.addWidget(self.group("PyDMScatterPlot", scatter))
        return widget

    def image_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        for attribute in ("ushort_image_ro", "double_image_ro"):
            image = PyDMImageView(image_channel=self.ch(attribute))
            image.normalizeData = True
            layout.addWidget(self.group("PyDMImageView: {}".format(attribute), image))
        return widget

    @staticmethod
    def group(title, content):
        box = QGroupBox(title)
        if isinstance(content, QWidget):
            layout = QVBoxLayout(box)
            layout.addWidget(content)
        else:
            box.setLayout(content)
        return box
