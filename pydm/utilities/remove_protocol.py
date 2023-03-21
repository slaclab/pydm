import re
import urllib

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
    Returns the Protocol, Address and optional subfield pieces of a Channel Address

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
    subfield : list, str
    """
    match = re.match('.*?://', address)
    protocol = None 
    addr = address
    subfield = None 

    if match:
        parsed_address = urllib.parse.urlparse(address)
        protocol = parsed_address.scheme 
        addr = parsed_address.netloc
        subfield = parsed_address.path 
        full_addr = parsed_address.netloc + parsed_address.path

        if subfield != '':
            subfield = subfield[1:].split('/')
    
    return protocol, addr, subfield, full_addr
