import json

from pydm.utilities.channel import parse_channel_config


def test_parse_channel_config():
    ret = parse_channel_config("ca://MTEST:Float", force_dict=True)
    assert ret == {"connection": {"protocol": "ca",
                                  "parameters": {"address": "MTEST:Float"}}}

    ret = parse_channel_config("ca://MTEST:Float", force_dict=False)
    assert ret == "ca://MTEST:Float"

    entry = {'connection': {'parameters': {'param1': 1,
                                           'param2': True,
                                           'param3': 'Test OK'},
                            'protocol': 'test'}}
    ret = parse_channel_config(json.dumps(entry), force_dict=True)
    assert ret == entry

    ret = parse_channel_config(json.dumps(entry), force_dict=False)
    assert ret == entry
