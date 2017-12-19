

class ExternalTool():

    def __init__(self, icon, name, group, use_with_widgets=True):
        self.icon = icon
        self.name = name
        self.group = group
        self.use_with_widgets = use_with_widgets

    def call(self, channels, values, sender):
        raise NotImplementedError

    def to_json(self):
        raise NotImplementedError

    def from_json(self, content):
        raise NotImplementedError
