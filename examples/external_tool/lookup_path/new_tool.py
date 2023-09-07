from pydm.tools import ExternalTool
from pydm.utilities.iconfont import IconFont


class DummyTool2(ExternalTool):
    def __init__(self):
        icon = IconFont().icon("code")
        name = "Dummy Tool 2"
        group = "Example"
        use_with_widgets = True
        use_without_widget = False
        super().__init__(
            icon=icon,
            name=name,
            group=group,
            use_with_widgets=use_with_widgets,
            use_without_widget=use_without_widget,
        )

    def call(self, channels, sender):
        print("Called Dummy Tool 2 from: {} with:".format(sender))
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
