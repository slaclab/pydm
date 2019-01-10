from __future__ import print_function
import os
import pkgutil
import sys
import types
import time
from inspect import isclass, signature, Parameter

import pytest

from qtpy.QtCore import Property, Qt
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QTabWidget, QWidget

from .. import widgets
from ..widgets.base import PyDMWidget


def get_all_widgets(base_class=QWidget, prefix='PyDM'):
    modules = pkgutil.iter_modules([os.path.dirname(widgets.__file__)])
    ret = []
    for (_, name, _) in modules:
        module_name = 'pydm.widgets.{}'.format(name)
        __import__(module_name)
        module = sys.modules[module_name]
        print(module_name, module)
        for name in dir(module):
            if not name.startswith(prefix):
                continue

            obj = getattr(module, name)

            if (isclass(obj) and issubclass(obj, base_class)
                    and obj is not base_class):
                print(module_name, name)
                ret.append(obj)
    return ret


all_widgets = get_all_widgets()


def find_properties(cls):
    properties = {}
    for attr in dir(cls):
        obj = getattr(cls, attr)
        if isinstance(obj, Property):
            properties[attr] = dict(
                type_=obj.type,
                read_only=obj.fset is None,
            )

    return properties


type_to_values = {
    bool: [True, False],
    'bool': [True, False],
    int: [0, 1],
    float: [0.01, 1.0],
    str: ['{}', '{"a":1}'],
    QColor: [QColor(0, 0, 0), QColor(100, 100, 100)],
    Qt.Orientation: [Qt.Vertical, Qt.Horizontal],
    QTabWidget.TabPosition: [QTabWidget.North,
                             QTabWidget.South],
    'QStringList': [['a', 'b'], ],
}


method_parameters = [0, 1]

special_values = {
    'channel': ['ca://MTEST:Float'],
    'rules': '',
}


initial_values = {'PyDMWaveformTable': [0, 1, 2]}

skip_methods = {'paintEvent', 'init_for_designer', 'exportClicked',
                'validate_password', 'confirm_dialog', }

special_method_args = {
    'alarm_severity_changed': [[PyDMWidget.ALARM_NONE, ],
                               [PyDMWidget.ALARM_MINOR, ],
                               [PyDMWidget.ALARM_MAJOR, ],
                               [PyDMWidget.ALARM_INVALID, ],
                               [PyDMWidget.ALARM_DISCONNECTED, ],
                               ],
    'alarmSeverityChanged': [[PyDMWidget.ALARM_NONE, ],
                             [PyDMWidget.ALARM_MINOR, ],
                             [PyDMWidget.ALARM_MAJOR, ],
                             [PyDMWidget.ALARM_INVALID, ],
                             [PyDMWidget.ALARM_DISCONNECTED, ],
                             ],
    'value_changed': [[0]],
}


@pytest.mark.xfail(reason='smoke test', strict=False)
@pytest.mark.parametrize("cls", all_widgets)
def test_smoke_widget(qtbot, cls, call_methods=False):
    widget = cls()

    # qtbot.addWidget(widget)
    print('Testing', cls, widget)

    initial_value = initial_values.get(cls.__name__, 0)

    print('Setting initial value of', widget, 'to', initial_value)
    with qtbot.capture_exceptions():
        try:
            widget.value_changed(initial_value)
        except (AttributeError, NameError):
            pass

        properties = find_properties(cls)
        for attr, prop_info in properties.items():
            print()
            print('-- Attribute:', attr)
            # Call the getter:
            try:
                value = getattr(widget, attr)
            except Exception as ex:
                print('* {}: getter failed: {} {}'.format(attr, type(ex), ex))
                continue

            print(attr, prop_info, value)
            if not prop_info['read_only']:
                type_ = prop_info['type_']
                if attr in special_values:
                    values = special_values[attr]
                else:
                    try:
                        values = type_to_values[type_]
                    except KeyError:
                        print('* No values for type {}; skipping'.format(type_))
                        continue

                # Call the setter once per value:
                for value in values:
                    try:
                        setattr(widget, attr, value)
                    except Exception as ex:
                        print('Setter failed!', attr, type_, value, type(ex), ex)

        if call_methods:
            other_attrs = set(dir(widget)) - set(properties) - skip_methods
            for attr in other_attrs:
                try:
                    method = getattr(widget, attr)
                except Exception as ex:
                    print('Skipping', attr, type(ex), ex)
                    continue

                if not isinstance(method, types.MethodType):
                    continue
                elif attr.endswith('Event'):
                    continue

                if attr in special_method_args:
                    arg_options = special_method_args[attr]
                else:
                    try:
                        sig = signature(method)
                    except ValueError:
                        # built-in method; skip
                        continue
                    parameters = [param
                                  for param in sig.parameters.values()
                                  if param.name != 'self' and
                                  param.kind != Parameter.KEYWORD_ONLY]

                    if len(parameters) == 0:
                        arg_options = [[]]
                    elif len(parameters) == 1:
                        # Try sending every type we know about
                        arg_options = [[param] for param in method_parameters]
                    else:
                        print('Skipping complex method', attr)
                        continue

                for args in arg_options:
                    print('Calling method', attr, 'with args', args, end=': ')
                    sys.stdout.flush()
                    try:
                        print('Returned:', method(*args))
                    except Exception as ex:
                        print('Failed', type(ex), ex)

        try:
            print('Closing widget')
            widget.close()
            print('Marking for deletion')
            widget.deleteLater()
            time.sleep(0.1)
            del widget
        except Exception as ex:
            print('Exception on closing widget', type(ex), ex)
