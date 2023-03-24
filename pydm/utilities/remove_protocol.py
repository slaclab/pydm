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
    _, addr, _ = protocol_and_address(addr)
    return addr


def protocol_and_address(address):
    """
    Returns the protocol, address and parsed address 

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
    parsed_address = None
    
    if match:
        parsed_address = urllib.parse.urlparse(address)
        protocol = parsed_address.scheme 
        
        if protocol == 'calc' or protocol == 'loc':
            addr = parsed_address.netloc + parsed_address.query
        else:
            addr = parsed_address.netloc

    
    return protocol, addr, parsed_address
