import logging
import functools

import collections

from qtpy.QtCore import QObject, QThread, QMutex, Signal, QMutexLocker
from qtpy.QtWidgets import QApplication

from .channel import PyDMChannel
from ..utilities import is_pydm_app

import numpy as np
import math

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
        None
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
    rule_signal = Signal(dict)

    def __init__(self):
        QThread.__init__(self)
        self.map_lock = QMutex()
        self.widget_map = dict()

    def register(self, widget, rules):
        if widget in self.widget_map:
            self.unregister(widget)

        with QMutexLocker(self.map_lock):
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
                    item['channels'].append(c)
                    c.connect()

                self.widget_map[widget].append(item)

    def unregister(self, widget):
        with QMutexLocker(self.map_lock):
            w_data = self.widget_map.pop(widget)

        for rule in w_data:
            for ch in rule['channels']:
                ch.disconnect()

        del w_data

    def run(self):
        while not self.isInterruptionRequested():
            with QMutexLocker(self.map_lock):
                for widget in self.widget_map:
                    for rule in self.widget_map[widget]:
                        if rule['calculate']:
                            self.calculate_expression(widget, rule)
            self.msleep(33)  # 30Hz

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
        with QMutexLocker(self.map_lock):
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

        .. warning

            This method mutates the input rule in-place

        Returns
        -------
        None
        """
        rule['calculate'] = False
        eval_env = {'np': np,
                    'ch': rule['values']}
        eval_env.update({k: v
                         for k, v in math.__dict__.items()
                         if k[0] != '_'})

        try:
            expression = rule['rule']['expression']
            name = rule['rule']['name']
            prop = rule['rule']['property']

            val = eval(expression, eval_env)
            payload = {'widget': widget, 'name': name, 'property': prop,
                       'value': val}
            self.rule_signal.emit(payload)
        except Exception as e:
            logger.exception("Error while evaluating Rule.")
