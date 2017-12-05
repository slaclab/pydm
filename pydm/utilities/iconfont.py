"""
iconfont provides a barebones system to get QIcons from icon fonts (like Font Awesome).
The inspiration and methodology come from the 'QtAwesome' module, which does exactly this, but
is a little too big, complicated, and flexible for PyDM's needs.
"""
import os
import sys
import json
from ..PyQt.QtGui import QFontDatabase, QIconEngine, QPixmap, QPainter, QColor, QFont, QIcon
from ..PyQt.QtCore import Qt, QRect, QPoint, qRound
if sys.version_info[0] == 3:
    unichr = chr


class IconFont(object):
    """IconFont represents an icon font.  Users will generally want
    to use IconFont.icon() to get a QIcon object for the character they want."""
    __instance = None

    def __init__(self):
        if self.__initialized:
            return
        self.font_file = "fontawesome.ttf"  # specify these relative to this file.
        self.charmap_file = "fontawesome-charmap.json"
        self.font_name = None
        self.char_map = None
        self.load_font(self.font_file, self.charmap_file)
        self.__initialized = True

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(IconFont)
            cls.__instance.__initialized = False
        return cls.__instance

    def load_font(self, ttf_filename, charmap_filename):

        def hook(obj):
            result = {}
            for key in obj:
                result[key] = unichr(int(obj[key], 16))
            return result

        if self.char_map is None:
            font_id = QFontDatabase.addApplicationFont(os.path.join(os.path.dirname(os.path.realpath(__file__)), ttf_filename))
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                self.font_name = font_families[0]
            else:
                raise IOError("Could not load ttf file for icon font.")
            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), charmap_filename), 'r') as codes:
                self.char_map = json.load(codes, object_hook=hook)

    def get_char_for_name(self, name):
        if name in self.char_map:
            return self.char_map[name]
        else:
            print(self.char_map)
            raise ValueError("Invalid icon name for font.")

    def font(self, size):
        font = QFont(self.font_name)
        font.setPixelSize(size)
        return font

    def icon(self, name):
        char = self.get_char_for_name(name)
        engine = CharIconEngine(self, char)
        return QIcon(engine)


class CharIconEngine(QIconEngine):
    """Subclass of QIconEngine that is designed to draw characters from icon fonts."""

    def __init__(self, icon_font, char):
        super(CharIconEngine, self).__init__()
        self.icon_font = icon_font
        self.char = char

    def paint(self, painter, rect, mode, state):
        painter.save()
        if mode == QIcon.Disabled:
            color = QColor(150, 150, 150)
        else:
            color = QColor(90, 90, 90)
        painter.setPen(color)
        scale_factor = 1.0
        draw_size = 0.875 * qRound(rect.height() * scale_factor)
        painter.setFont(self.icon_font.font(draw_size))
        painter.setOpacity(1.0)
        painter.drawText(rect, Qt.AlignCenter | Qt.AlignVCenter, self.char)
        painter.restore()

    def pixmap(self, size, mode, state):
        pm = QPixmap(size)
        pm.fill(Qt.transparent)
        self.paint(QPainter(pm), QRect(QPoint(0, 0), size), mode, state)
        return pm
