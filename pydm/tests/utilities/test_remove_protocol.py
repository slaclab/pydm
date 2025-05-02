from pydm.utilities.remove_protocol import remove_protocol
from pydm.utilities.remove_protocol import protocol_and_address
from pydm.utilities.remove_protocol import parsed_address


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
    assert out == ("foo", "bar", "", "")

    out = parsed_address("foo://bar#baz")
    assert out == ("foo", "bar#baz", "", "")

    out = parsed_address("foo:///aj")
    assert out == ("foo", "", "/aj", "")

    out = parsed_address("foo://rd?question!")
    assert out == ("foo", "rd", "", "question!")

    out = parsed_address("alpha://beta/delta?gamma")
    assert out.scheme == "alpha" and out.netloc == "beta" and out.path == "/delta" and out.query == "gamma"

    out = parsed_address("foo://test:channel.{'f': {'lo':0, 'hi':10} }?and_query_too")
    assert out == ("foo", "test:channel.{'f': {'lo':0, 'hi':10} }", "", "and_query_too")

    out = parsed_address("foo://TEST:PV[3]")
    assert out == ("foo", "TEST:PV[3]", "", "")

    out = parsed_address("loc://my_variable_name?type=variable_type&init=initial_values")
    assert out == ("loc", "my_variable_name", "", "type=variable_type&init=initial_values")
