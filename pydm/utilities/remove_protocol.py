import collections
import re
import urllib
from pydm import config


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
    match = re.match(".*?://", address)
    protocol = None
    addr = address
    if match:
        protocol = match.group(0)[:-3]
        addr = address.replace(match.group(0), "")

    return protocol, addr


BasicURI = collections.namedtuple("BasicURI", ["scheme", "netloc", "path", "query"])


def parsed_address(address):
    """
    Returns the given address parsed into a BasicURI named tuple.

    Parameters
    ----------
    address : str
        The address from which to remove the address prefix.

    Returns
    -------
    parsed_address : tuple
    """
    if not isinstance(address, str):
        return None

    match = re.match(".*?://", address)
    if not match:
        if not config.DEFAULT_PROTOCOL:
            return None
        address = config.DEFAULT_PROTOCOL + "://" + address

    # scheme://netloc/path?query will decompose into "scheme", "netloc", "/path", "query"
    # scheme is required. netloc, path, and query are each optional but have to appear in this order
    components = re.match(r"(.*?)://([^/?]*)(?:(/[^?]*)?(?:\?(.*))?)?", address)
    if not components:
        return None

    return BasicURI(
        scheme=(components.group(1) or ""),
        netloc=(components.group(2) or ""),
        path=(components.group(3) or ""),
        query=(components.group(4) or ""),
    )
