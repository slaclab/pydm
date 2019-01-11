from __future__ import print_function
import inspect
import os
import pkgutil
import sys
import time
import types

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

            if (inspect.isclass(obj) and issubclass(obj, base_class)
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
}


@pytest.mark.xfail(reason='smoke test', strict=False)
@pytest.mark.parametrize("cls", all_widgets)
def test_smoke_widget(qtbot, cls, call_methods=True):
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
                elif attr in ('value_changed', 'channelValueChanged'):
                    arg_options = [[initial_value]]
                else:
                    try:
                        try:
                            # Python 3.0+
                            argspec = inspect.getfullargspec(method)
                        except AttributeError:
                            # Python 2.7
                            argspec = inspect.getargspec(method)
                    except ValueError:
                        # built-in method; skip
                        continue

                    args = argspec.args
                    if 'self' in args:
                        args.remove('self')

                    if len(args) == 0:
                        arg_options = [[]]
                    elif len(args) == 1:
                        # Try sending every type we know about
                        arg_options = [[param] for param in method_parameters]
                    else:
                        print('Skipping complex method', attr)
                        continue

                for args in arg_options:
                    print('Calling method', attr, 'with args', args, end=': ')
                    sys.stdout.flush()
                    try:
                        ret = method(*args)
                    except Exception as ex:
                        print('Failed', type(ex), ex)
                    else:
                        print('Returned:', ret)
                        if isinstance(ret, QWidget) and ret is not widget:
                            try:
                                print('Closing likely new widget')
                                ret.close()
                            except Exception:
                                pass
        try:
            print('Closing widget')
            widget.close()
            print('Marking for deletion')
            widget.deleteLater()
            time.sleep(0.1)
            del widget
            time.sleep(0.5)
        except Exception as ex:
            print('Exception on closing widget', type(ex), ex)
