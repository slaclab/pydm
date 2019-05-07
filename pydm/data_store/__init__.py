class DataKeys(object):
    """
    Enum class which holds the keys expected by the PyDMWidgets when used with
    a structured data to parse the data in search for the needed fields.
    """
    CONNECTION = 'CONNECTION'
    VALUE = 'VALUE'
    SEVERITY = 'SEVERITY'
    WRITE_ACCESS = 'WRITE_ACCESS'
    ENUM_STRINGS = 'ENUM_STRINGS'
    UNIT = 'UNIT'
    PRECISION = 'PRECISION'
    UPPER_LIMIT = 'UPPER_LIMIT'
    LOWER_LIMIT = 'LOWER_LIMIT'

    @staticmethod
    def generate_introspection_for(connection_key=None, value_key=None,
                                   severity_key=None, write_access_key=None,
                                   enum_strings_key=None, unit_key=None,
                                   precision_key=None, upper_limit_key=None,
                                   lower_limit_key=None
                                   ):
        """
        Generates an introspection dictionary for a given set of keys.
        This is used by PyDMWidgets to map the needed keys in a structured
        data source into the fields needed.

        Parameters
        ----------
        connection_key : str
            The key for the connection status information at the data
            dictionary
        value_key : str
            The key for the value information at the data dictionary
        severity_key : str
            The key for the severity information at the data dictionary
        write_access_key : str
            The key for the write access information at the data dictionary
        enum_strings_key : str
            The key for the enum strings information at the data dictionary
        unit_key : str
            The key for the engineering unit information at the data dictionary
        precision_key : str
            The key for the precision information at the data dictionary
        upper_limit_key : str
            The key for the upper limit information at the data dictionary
        lower_limit_key : str
            The key for the lower limit information at the data dictionary

        Returns
        -------
        introspection : dict

        """
        lookup_table = [
            (connection_key, DataKeys.CONNECTION),
            (value_key, DataKeys.VALUE),
            (severity_key, DataKeys.SEVERITY),
            (write_access_key, DataKeys.WRITE_ACCESS),
            (enum_strings_key, DataKeys.ENUM_STRINGS),
            (unit_key, DataKeys.UNIT),
            (precision_key, DataKeys.PRECISION),
            (upper_limit_key, DataKeys.UPPER_LIMIT),
            (lower_limit_key, DataKeys.LOWER_LIMIT)
        ]
        introspection = dict()

        for val, key in lookup_table:
            if val:
                introspection[key] = val

        return introspection


DEFAULT_INTROSPECTION = {k: v for k, v in DataKeys.__dict__.items()
                         if isinstance(v, str) and not k.startswith('_')}


class _DataStore(object):

    def __init__(self):
        self._data = {}
        self._introspection = {}

    def introspect(self, address):
        """
        Query the introspection mapping about the information for a given
        address.

        Parameters
        ----------
        address : str
            The address identifier.

        Returns
        -------
        introspection : dict or None
            If no information is found this method returns None
        """
        return self._introspection.get(address, None)

    def fetch(self, address):
        """
        Fetch the data associated with an address.

        Parameters
        ----------
        address : str
            The address identifier

        Returns
        -------
        data : dict
            If no information is found this method returns and empty dictionary
        """
        data = self._data.get(address, {})
        return data

    def fetch_with_introspection(self, address):
        """
        Fetch the data associated with an address and its introspection.

        Parameters
        ----------
        address : str
            The address identifier

        Returns
        -------
        data : dict
            If no information is found this returns an empty dictionary
        introspection : dict
            If no information is found this returns an empty dictionary
        """
        data = self.fetch(address)
        intro = self._introspection.get(address, {})
        return data, intro

    def update(self, address, data, introspection=None):
        """
        Update the cache with the new values for data and introspection.

        Parameters
        ----------
        address : str
            The address identifier.

        data : dict
            The data payload to be stored.

        introspection : dict, optional.
            The introspection payload to be stored.

        """
        self._data[address] = data
        if introspection:
            self._introspection[address] = introspection

    def remove(self, address):
        """
        Removes all data associated with a given address from the Data Store.

        Parameters
        ----------
        address : str
            The address identifier.

        """
        self._data.pop(address, None)
        self._introspection.pop(address, None)

    def __getitem__(self, item):
        return self.fetch(item)

    def __setitem__(self, key, value):
        if isinstance(value, tuple):
            self.update(key, value[0], value[1])
        elif isinstance(value, dict):
            self.update(key, value)
        else:
            raise ValueError("Invalid value.")

DataStore = _DataStore()