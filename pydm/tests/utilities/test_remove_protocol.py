from ...utilities.remove_protocol import remove_protocol


def test_remove_protocol():
    out = remove_protocol('foo://bar')
    assert (out == 'bar')

    out = remove_protocol('bar')
    assert (out == 'bar')

    out = remove_protocol('foo://bar://foo2')
    assert (out == 'bar://foo2')
