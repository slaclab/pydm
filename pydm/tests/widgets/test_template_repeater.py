import os
import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication
from ...widgets import PyDMSlider, PyDMTemplateRepeater

test_template_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "../test_data", "template.ui")
    
def test_template_file(qtbot):
    # Test that loading a template and setting data instantiates an instance
    # of the template.
    template_repeater = PyDMTemplateRepeater()
    qtbot.addWidget(template_repeater)
    template_repeater.templateFilename = test_template_path
    test_data = [{"devname": "test_device"}]
    template_repeater.data = test_data
    assert template_repeater.count() == len(test_data)
    slider = template_repeater.findChild(PyDMSlider, "bCtrlSlider")
    assert slider is not None
    assert slider.channel == "ca://{}:BCTRL".format(test_data[0]["devname"])