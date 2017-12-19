import os


class ExternalTool():

    def __init__(self, icon, name, group, author="", use_with_widgets=True):
        self.icon = icon
        self.name = name
        self.group = group
        self.author = author
        self.use_with_widgets = use_with_widgets

    def call(self, channels, sender):
        raise NotImplementedError

    def to_json(self):
        raise NotImplementedError

    def from_json(self, content):
        raise NotImplementedError

    def get_info(self):
        return {
            'author': self.author,
            'file': "",
            'group': self.group,
            'name': self.name
            }
