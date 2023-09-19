from pydm.tools import ExternalTool
from pydm.utilities.iconfont import IconFont


class DummyTool(ExternalTool):
    def __init__(self):
        icon = IconFont().icon("cogs")
        name = "Dummy Tool"
        group = "Example"
        use_with_widgets = False
        super().__init__(icon=icon, name=name, group=group, use_with_widgets=use_with_widgets)

    def call(self, channels, sender):
        print("Called Dummy Tool from: {} with:".format(sender))
        print("Channels: ", channels)
        print("My info: ", self.get_info())

    def to_json(self):
        return ""

    def from_json(self, content):
        print("Received from_json: ", content)

    def get_info(self):
        ret = ExternalTool.get_info(self)
        ret.update({"file": __file__})
        return ret


class DummyTool3(ExternalTool):
    def __init__(self):
        icon = None
        name = "Dummy Tool 3"
        group = ""
        use_with_widgets = False
        super().__init__(icon=icon, name=name, group=group, use_with_widgets=use_with_widgets)

    def call(self, channels, sender):
        print("Called Dummy Tool 3 from: {} with:".format(sender))
        print("Channels: ", channels)
        print("My info: ", self.get_info())

    def to_json(self):
        return ""

    def from_json(self, content):
        print("Received from_json: ", content)

    def get_info(self):
        ret = ExternalTool.get_info(self)
        ret.update({"file": __file__})
        return ret
