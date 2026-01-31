#######################
PyDMByteIndicator
#######################

.. autoclass:: pydm.widgets.byte.PyDMByteIndicator
   :members:
   :show-inheritance:


.. note::
   See `QWidget Documentation <https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QWidget.html>`_ for all inherited properties and methods.
   
   
   
   

# Remove the separate PyDMBlinkByteIndicator class since its functionality is now integrated into PyDMByteIndicator
# PyDMBlinkByteIndicator is no longer needed

1. Core Blinking Mechanism
   - Added QTimer for timed color switching
   - _toggle_blink_color() method alternates between two blink colors
   - _start_blinking() and _stop_blinking() methods control blinking start/stop

2. Blinking Configuration Properties
   - blinkOnChange: Enables or disables blinking functionality
   - toggleMode: Selects blinking pattern:
     * Normal mode: Starts blinking when value changes from 1→0, stops when 0→1
     * Toggle mode: Starts blinking when value changes from 0→1, stops when 1→0
   - blinkColor1 and blinkColor2: Two alternating blink colors
   - blinkInterval: Blinking interval time in milliseconds

3. Value Change Handling
   - In value_changed() method, monitors transitions between 0 and 1 values
   - Automatically starts/stops blinking based on selected mode and value transitions
   - Maintains previous value state for comparison

4. Indicator Color Update
   - In update_indicators() method, determines which bits should blink
   - Toggle mode: Only bits with value 1 blink
   - Normal mode: Only bits with value 0 blink
   - Non-blinking bits display normal on/off colors

5. Backward Compatibility
   - Default blinkOnChange = False ensures existing code remains unaffected
   - All original functionality (layout, orientation, endianness, labels) preserved
   - Blinking only activates when explicitly setting blinkOnChange = True
   - Single unified class instead of separate classes for cleaner maintenance
