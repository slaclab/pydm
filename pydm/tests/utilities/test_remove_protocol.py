from ...utilities.remove_protocol import remove_protocol
from ...utilities.remove_protocol import protocol_and_address
from ...utilities.remove_protocol import parsed_address


def test_remove_protocol():
    out = remove_protocol("foo://bar")
    assert out == "bar"

    out = remove_protocol("bar")
    assert out == "bar"

    out = remove_protocol("foo://bar://foo2")
    assert out == "bar://foo2"


def test_protocol_and_address():
    out = protocol_and_address("foo://bar")
    assert out == ("foo", "bar")

    out = protocol_and_address("foo:/bar")
    assert out == (None, "foo:/bar")


def test_parsed_address():
    out = parsed_address(1)
    assert out is None

    out = parsed_address("foo:/bar")
    assert out is None

    out = parsed_address("foo://bar")
    assert out == ("foo", "bar", "", "", "", "")
