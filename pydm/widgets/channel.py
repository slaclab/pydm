class PyDMChannel:
  def __init__(self, address=None, connection_slot=None, value_slot=None, waveform_slot=None, severity_slot=None):
    self.address = address
    self.connection_slot = connection_slot
    self.value_slot = value_slot
    self.severity_slot = severity_slot
    self.waveform_slot = waveform_slot
    