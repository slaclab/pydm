import json
import logging
import functools
import weakref

from qtpy.QtCore import QThread, QMutex, Signal, QMutexLocker
from qtpy.QtWidgets import QWidget, QApplication

from .channel import PyDMChannel

import pydm.data_plugins

import numpy as np
import math

logger = logging.getLogger(__name__)


def unregister_widget_rules(widget):
    """
    Given a widget to start from, traverse the tree of child widgets,
    and try to unregister rules to any widgets.

    Parameters
    ----------
    widget : QWidget
    """
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
        try:
            if hasattr(child_widget, 'rules'):
                if child_widget.rules:
                    RulesDispatcher().unregister(weakref.ref(child_widget))
        except Exception:
            pass


def register_widget_rules(widget):
    """
    Given a widget to start from, traverse the tree of child widgets,
    and try to unregister rules to any widgets.

    Parameters
    ----------
    widget : QWidget
    """
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
        try:
            if hasattr(child_widget, 'rules'):
                if child_widget.rules:
                    rules = json.loads(child_widget.rules)
                    RulesDispatcher().register(child_widget, rules)
        except Exception:
            pass


class RulesDispatcher(object):
    """
    Singleton class responsible for handling all the interactions with the
    RulesEngine and dispatch the payloads from the rules thread to the widget.
    """
    __instance = None

    def __init__(self):
        if self.__initialized:
            return
        self.rules_engine = RulesEngine()
        self.rules_engine.rule_signal.connect(self.dispatch)
        self.rules_engine.start()
        self.__initialized = True

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(RulesDispatcher)
            cls.__instance.__initialized = False
        return cls.__instance

    def register(self, widget, rules):
        """
        Register widget rules with the RulesEngine thread.

        Parameters
        ----------
        widget : QWidget
            The widget that is associated with the rules.
        rules : list
            List of dictionaries containing the definition of the rules.

        Returns
        -------
        None
        """
        self.rules_engine.register(widget, rules)

    def unregister(self, widget):
        """
        Unregister widget rules with the RulesEngine thread.

        Parameters
        ----------
        widget : QWidget or weakref
            The weakref to widget or widget that is associated with the rules.

        """
        if isinstance(widget, weakref.ref):
            self.rules_engine.unregister(widget)
        else:
            self.rules_engine.unregister(weakref.ref(widget))

    def dispatch(self, payload):
        """
        Callback invoked when the RulesEngine evaluate a rule and send new value
        to the widget. This dispatcher is a bridge between the Thread and the
        widgets.

        Parameters
        ----------
        payload : dict
            The payload data including the widget for method invoking.
        """
        try:
            widget = payload.pop('widget')
            if isinstance(widget, weakref.ref):
                widget_ref = widget
                widget = widget()
            if widget is None: # Widget is dead... lets unregister the ref
                self.rules_engine.unregister(widget_ref)
            else:
                widget.rule_evaluated(payload)
        except RuntimeError as ex:
            logger.debug("Widget reference was gone but not yet for Python.")
        except Exception as ex:
            logger.exception("Error at RulesDispatcher.")


class RulesEngine(QThread):
    """
    RulesEngine inherits from QThread and is responsible evaluating the rules
    for all the widgets in the application.

    Signals
    -------
    rule_signal : dict
        Emitted when a new value for the property is calculated by the engine.
    """
    rule_signal = Signal(dict)

    def __init__(self):
        QThread.__init__(self)
        self.app = QApplication.instance()
        self.app.aboutToQuit.connect(self.requestInterruption)
        self.map_lock = QMutex()
        self.widget_map = dict()

    def widget_destroyed(self, ref):
        self.unregister(ref)

    def register(self, widget, rules):
        widget_ref = weakref.ref(widget, self.widget_destroyed)
        if widget_ref in self.widget_map:
            self.unregister(widget_ref)

        rules_db = []
        for idx, rule in enumerate(rules):
            channels_list = rule.get('channels', [])

            item = dict()
            item['rule'] = rule
            initial_val = rule.get('initial_value', "").strip()
            name = rule.get('name')
            prop = rule.get('property')
            item['initial_value'] = initial_val
            item['calculate'] = False
            item['values'] = [None] * len(channels_list)
            item['enums'] = [None] * len(channels_list)
            item['conn'] = [False] * len(channels_list)
            item['channels'] = []

            for ch_idx, ch in enumerate(channels_list):
                conn_cb = functools.partial(self.callback_conn, widget_ref,
                                            idx, ch_idx)
                value_cb = functools.partial(self.callback_value, widget_ref,
                                             idx, ch_idx, ch['trigger'])
                enums_cb = functools.partial(self.callback_enum, widget_ref,
                                             idx, ch_idx)
                c = PyDMChannel(ch['channel'], connection_slot=conn_cb,
                                value_slot=value_cb, enum_strings_slot=enums_cb)
                item['channels'].append(c)
            rules_db.append(item)
            if initial_val:
                self.emit_value(widget_ref, name, prop, initial_val)

        if rules_db:
            self.widget_map[widget_ref] = rules_db
            for rule in rules_db:
                for ch in rule['channels']:
                    ch.connect()

    def unregister(self, widget_ref):
        # If hash() is called the first time only after the object was
        # deleted, the call will raise TypeError.
        # We should just ignore it.
        w_data = None
        try:
            w_data = self.widget_map.pop(widget_ref, None)
        except TypeError:
            pass

        if not w_data:
            return

        for rule in w_data:
            for ch in rule['channels']:
                ch.disconnect(destroying=widget_ref() is None)

        del w_data

    def run(self):
        while not self.isInterruptionRequested():
            w_map = self.widget_map.copy()
            for widget_ref, rules in w_map.items():
                for idx, rule in enumerate(rules):
                    if rule['calculate']:
                        self.calculate_expression(widget_ref, idx, rule)
            self.msleep(33)  # 30Hz

    def callback_enum(self, widget_ref, index, ch_index, enums):
        """
        Callback executed when a channel receives a new enum_string.

        Parameters
        ----------
        widget_ref : weakref
            A weakref to the widget owner of the rule.
        index : int
            The index of the rule being processed.
        ch_index : int
            The channel index on the list for this rule.
        trigger : bool
            Whether or not this channel should trigger a calculation of the
            expression
        value : any
            The new value for this channel.

        Returns
        -------
        None
        """
        try:
            w_map = self.widget_map[widget_ref]
            w_map[index]['enums'][ch_index] = enums
            if not all(w_map[index]['conn']):
                self.warn_unconnected_channels(widget_ref, index)
                return
            w_map[index]['calculate'] = True
        except (KeyError, IndexError):
            pass

    def callback_value(self, widget_ref, index, ch_index, trigger, value):
        """
        Callback executed when a channel receives a new value.

        Parameters
        ----------
        widget_ref : weakref
            A weakref to the widget owner of the rule.
        index : int
            The index of the rule being processed.
        ch_index : int
            The channel index on the list for this rule.
        trigger : bool
            Whether or not this channel should trigger a calculation of the
            expression
        value : any
            The new value for this channel.

        Returns
        -------
        None
        """
        try:
            w_map = self.widget_map[widget_ref]
            w_map[index]['values'][ch_index] = value
            if trigger:
                if not all(w_map[index]['conn']):
                    self.warn_unconnected_channels(widget_ref, index)
                    return
                w_map[index]['calculate'] = True
        except (KeyError, IndexError):
            pass

    def callback_conn(self, widget_ref, index, ch_index, value):
        """
        Callback executed when a channel connection status is changed.

        Parameters
        ----------
        widget_ref : weakref
            A weakref to the widget owner of the rule.
        index : int
            The index of the rule being processed.
        ch_index : int
            The channel index on the list for this rule.
        value : bool
            Whether or not this channel is connected.

        Returns
        -------
        None
        """
        try:
            self.widget_map[widget_ref][index]['conn'][ch_index] = value
        except (KeyError, IndexError):
            # widget_ref was destroyed
            pass

    def warn_unconnected_channels(self, widget_ref, index):
        logger.debug(
            "Rule '%s': Not all channels are connected, skipping execution.",
            self.widget_map[widget_ref][index]['rule']['name'])

    def calculate_expression(self, widget_ref, idx, rule):
        """
        Evaluate the expression defined by the rule and emit the `rule_signal`
        with the new value.

        .. warning

            This method mutates the input rule in-place

        Returns
        -------
        None
        """
        rule['calculate'] = False

        vals = rule['values']
        enums = rule['enums']

        calc_vals = []
        for en, val in zip(enums, vals):
            try:
                calc_vals.append(en[val])
                continue
            except:
                calc_vals.append(val)

        eval_env = {'np': np,
                    'ch': calc_vals}
        eval_env.update({k: v
                         for k, v in math.__dict__.items()
                         if k[0] != '_'})

        try:
            expression = rule['rule']['expression']
            name = rule['rule']['name']
            prop = rule['rule']['property']
            val = eval(expression, eval_env)
            self.emit_value(widget_ref, name, prop, val)
        except Exception as e:
            logger.exception("Error while evaluating Rule.")

    def emit_value(self, widget_ref, name, prop, val):
        """
        Emit the payload with the new value for the property.

        Parameters
        ----------
        widget_ref : weakref
            A weakref to the widget owner of the rule.
        name : str
            The Rule name
        prop : str
            The Rule property
        val : object
            The value to emit
        """
        payload = {'widget': widget_ref, 'name': name, 'property': prop,
                   'value': val}
        self.rule_signal.emit(payload)
