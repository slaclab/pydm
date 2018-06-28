import logging
import functools

from ..PyQt.QtCore import QThread, pyqtSignal
from ..PyQt.QtGui import QApplication

from .channel import PyDMChannel
from ..utilities import is_pydm_app

import numpy as np
from math import *

logger = logging.getLogger(__name__)


class RulesEngine(QThread):
    """
    RulesEngine inherits from QThread and is responsible for monitoring the
    channels associated with a rule, evaluate the expression when new values
    arrive and emit the signal for the widget so it can be updated properly.

    Parameters
    ----------
    rule_map : dict
        The dictionary containing the rule information needed for the engine.

    Signals
    -------
    rule_signal : dict
        Emitted when a new value for the property is calculated by the engine.
    """
    rule_signal = pyqtSignal(dict)

    def __init__(self, rule_map):
        QThread.__init__(self)
        if rule_map is None or not isinstance(rule_map, dict):
            raise ValueError("Invalid format for rule_map. Dictionary expected")
        # Enables termination of the current thread
        self.setTerminationEnabled(True)

        # Reference to App so we can establish the connection with the channel
        self.app = QApplication.instance()

        # Flag to control whether or not we should evaluate the expression
        self.should_calculate = False

        # Definitions for this Action Thread
        self.rule_map = rule_map
        self.name = rule_map.get('name', None)
        self.property = rule_map.get('property', None)
        self.expression = rule_map.get('expression', None)
        self.channels_list = rule_map.get('channels', [])

        # Buffer for data coming from the channels
        self.channels_connection = [False] * len(self.channels_list)
        self.channels_value = [None] * len(self.channels_list)

        self.channels = []

        for idx, ch in enumerate(self.channels_list):
            partial_connection = functools.partial(self.channel_conn_callback,
                                                   idx, ch['channel'],
                                                   ch['trigger'])
            partial_value = functools.partial(self.channel_value_callback,
                                              idx, ch['channel'], ch['trigger'])
            c = PyDMChannel(ch['channel'],
                            connection_slot=partial_connection,
                            value_slot=partial_value)
            if is_pydm_app():
                self.app.add_connection(c)
            self.channels.append(c)

    def channel_conn_callback(self, index, channel_name, trigger, value):
        """
        Callback executed when a channel connection status is changed.

        Parameters
        ----------
        index : int
            The channel index on the list for this rule.
        channel_name : str
            The channel address.
        trigger : bool
            Whether or not this channel should trigger a calculation of the
            expression
        value : bool
            Whether or not this channel is connected.

        Returns
        -------
        None
        """
        self.channels_connection[index] = value

    def channel_value_callback(self, index, channel_name, trigger, value):
        """
        Callback executed when a channel receives a new value.

        Parameters
        ----------
        index : int
            The channel index on the list for this rule.
        channel_name : str
            The channel address.
        trigger : bool
            Whether or not this channel should trigger a calculation of the
            expression
        value : any
            The new value for this channel.

        Returns
        -------
        None
        """
        self.channels_value[index] = value
        if trigger:
            if not all(self.channels_connection):
                logger.error(
                    "Rule %s: Not all channels are connected, skipping execution.",
                    self.name)
                return
            self.should_calculate = True

    def run(self):
        """
        Main loop of the RulesEngine which runs at 30Hz until a interruption is
        requested and calculates the expression if a new value is available at
        one of the trigger channels.

        Returns
        -------
        None
        """
        while not self.isInterruptionRequested():
            if self.should_calculate:
                self.calculate_expression()
            QThread.msleep(33)  # 30Hz

    def calculate_expression(self):
        """
        Evaluate the expression defined by the rule and emit the `rule_signal`
        with the new value.

        Returns
        -------
        None
        """
        self.should_calculate = False
        ch = self.channels_value
        try:
            val = eval(self.expression)
            payload = {'name': self.name, 'property': self.property, 'value': val}
            self.rule_signal.emit(payload)
        except Exception as e:
            logger.error("Error while evaluating Rule. Exception was: %s", e)
