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

    name = addr.split("://", 1)  # maxsplit = 1... removes only the first occurrence
    name = ''.join(name[1:]) if len(name) > 1 else addr
    return name
