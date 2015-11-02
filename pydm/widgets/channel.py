class PyDMChannel:
  def __init__(self, address=None, connection_slot=None, value_slot=None, waveform_slot=None, severity_slot=None, write_access_slot=None, enum_strings_slot=None, unit_slot=None, value_signal=None):
    self.address = address
    self.connection_slot = connection_slot
    self.value_slot = value_slot
    self.severity_slot = severity_slot
    self.waveform_slot = waveform_slot
    self.write_access_slot = write_access_slot
    self.enum_strings_slot = enum_strings_slot
    self.value_signal = value_signal
    self.unit_slot = unit_slot
    