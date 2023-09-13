from pydm.tools import ExternalTool
from pydm.utilities.iconfont import IconFont


class RootTool(ExternalTool):
    def __init__(self):
        icon = IconFont().icon("code")
        name = "Root Tool"
        group = ""
        use_with_widgets = True
        super().__init__(icon=icon, name=name, group=group, use_with_widgets=use_with_widgets)

    def call(self, channels, sender):
        print("Called Root Tool from: {} with:".format(sender))
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
