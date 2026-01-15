#######################
PyDMByteIndicator
#######################

.. autoclass:: pydm.widgets.byte.PyDMByteIndicator
   :members:
   :show-inheritance:


.. note::
   See `QWidget Documentation <https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QWidget.html>`_ for all inherited properties and methods.
   
   
   
   
The PyDMBlinkByteIndicator widget extends PyDM's byte indicator functionality by adding a blinking visual effect when the displayed value changes. Here are the key features:

A. Core Blinking Functionality:
A1. Dual-mode blinking:

  Normal mode: Starts blinking on a falling edge (1→0 transition) and stops on rising edge (0→1)

  Toggle mode: Starts blinking on a rising edge (0→1) and stops on falling edge (1→0)
A2. Configurable blinking: Two alternating colors with adjustable interval

A3. Visual feedback: Provides immediate visual indication of state transitions

B. How It Works:
B1. Value transition detection: Monitors bit value changes

B2. Timer-based animation: Uses QTimer to alternate between two colors at specified intervals

B3. Flexible configuration: Multiple properties allow customization of blinking behavior

C. Use Cases:
C1. Alarm indicators: Blinking draws attention to changing states

C2. Status monitoring: Visual feedback for bit transitions

C3. Control system interfaces: Enhanced visibility for important state changes   
