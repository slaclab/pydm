import json

from . import protocol_and_address
from .. import data_plugins

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


def parse_channel_config(value, force_dict=False):
    try:
        config = json.loads(value)
    except JSONDecodeError:
        # Fallback to string channel config
        config = value
        if force_dict:
            protocol, address = protocol_and_address(value)
            config = {
                "connection":{
                    "protocol": protocol,
                    "parameters": {"address": address}
                }
            }
    return config


def get_plugin_repr(address):
    plugin = data_plugins.plugin_for_address(address)
    plugin_repr = plugin.get_repr(address)
    return plugin_repr
