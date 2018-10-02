import re

def remove_protocol(addr):
    """
    Removes the first occurrence of the protocol string ('://') from the string `addr`

    Parameters
    ----------
    addr : str
        The address from which to remove the address prefix.

    Returns
    -------
    str
    """
    _, addr = protocol_and_address(addr)
    return addr


def protocol_and_address(address):
    """
    Returns the Protocol and Address pieces of a Channel Address

    Parameters
    ----------
    address : str
        The address from which to remove the address prefix.

    Returns
    -------
    protocol : str
        The protocol used. None in case the protocol is not specified.
    addr : str
        The piece of the address without the protocol.
    """
    match = re.match('.*?://', address)
    protocol = None
    addr = address
    if match:
        protocol = match.group(0)[:-3]
        addr = address.replace(match.group(0), '')

    return protocol, addr