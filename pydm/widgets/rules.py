import logging
import functools

import collections

from ..PyQt.QtCore import QObject, QThread, QMutex, pyqtSignal
from ..PyQt.QtGui import QApplication

from .channel import PyDMChannel
from ..utilities import is_pydm_app

import numpy as np
from math import *

logger = logging.getLogger(__name__)


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
        bool
            True if all the rules were successfully registered, False otherwise.
        """
        self.rules_engine.register(widget, rules)

    def unregister(self, widget):
        """
        Unregister widget rules with the RulesEngine thread.

        Parameters
        ----------
        widget : QWidget
            The widget that is associated with the rules.

        """
        self.rules_engine.unregister(widget)

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
            widget.rule_evaluated(payload)
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
    rule_signal = pyqtSignal(dict)

    def __init__(self):
        QThread.__init__(self)
        # Reference to App so we can establish the connection with the channel
        self.app = QApplication.instance()
        self.map_lock = QMutex()
        self.widget_map = dict()

    def register(self, widget, rules):
        self.map_lock.lock()

        if widget in self.widget_map:
            self.unregister(widget, already_locked=True)


        self.widget_map[widget] = []

        for idx, rule in enumerate(rules):
            channels_list = rule.get('channels', [])

            item = dict()
            item['rule'] = rule
            item['calculate'] = False
            item['values'] = [None] * len(channels_list)
            item['conn'] = [False] * len(channels_list)
            item['channels'] = []

            for ch_idx, ch in enumerate(channels_list):
                conn_cb = functools.partial(self.callback_conn, widget, idx,
                                            ch_idx)
                value_cb = functools.partial(self.callback_value, widget, idx,
                                             ch_idx, ch['trigger'])
                c = PyDMChannel(ch['channel'], connection_slot=conn_cb,
                                value_slot=value_cb)
                if is_pydm_app():
                    self.app.add_connection(c)
                item['channels'].append(c)

            self.widget_map[widget].append(item)

        self.map_lock.unlock()

    def unregister(self, widget, already_locked=False):
        if not already_locked:
            self.map_lock.lock()
        try:
            w_data = self.widget_map.pop(widget)
            for rule in w_data:
                for ch in rule['channels']:
                    if is_pydm_app():
                        self.app.remove_connection(ch)
            del w_data
        except:
            pass

        if not already_locked:
            self.map_lock.unlock()

    def run(self):
        while not self.isInterruptionRequested():
            self.map_lock.lock()
            for widget in self.widget_map:
                for rule in self.widget_map[widget]:
                    if rule['calculate']:
                        self.calculate_expression(widget, rule)
            self.map_lock.unlock()
            self.msleep(33) # 30Hz

    def callback_value(self, widget, index, ch_index, trigger, value):
        """
        Callback executed when a channel receives a new value.

        Parameters
        ----------
        widget : QWidget
            The widget owner of the rule.
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
        self.widget_map[widget][index]['values'][ch_index] = value
        if trigger:
            if not all(self.widget_map[widget][index]['conn']):
                self.warn_unconnected_channels(widget, index)
                return
            self.widget_map[widget][index]['calculate'] = True

    def callback_conn(self, widget, index, ch_index, value):
        """
        Callback executed when a channel connection status is changed.

        Parameters
        ----------
        widget : QWidget
            The widget owner of the rule.
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
        self.widget_map[widget][index]['conn'][ch_index] = value

    def warn_unconnected_channels(self, widget, index):
        logger.error(
            "Rule '%s': Not all channels are connected, skipping execution.",
            self.widget_map[widget][index]['rule']['name'])

    def calculate_expression(self, widget, rule):
        """
        Evaluate the expression defined by the rule and emit the `rule_signal`
        with the new value.

        Returns
        -------
        None
        """
        ch = rule['values']
        rule['calculate'] = False
        try:
            expression = rule['rule']['expression']
            name = rule['rule']['name']
            property = rule['rule']['property']

            val = eval(expression)
            payload = {'widget': widget, 'name': name, 'property': property,
                       'value': val}
            self.rule_signal.emit(payload)
        except Exception as e:
            logger.exception("Error while evaluating Rule.")
