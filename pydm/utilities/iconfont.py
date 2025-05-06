"""
iconfont provides a barebones system to get QIcons from icon fonts (like Font Awesome).
The inspiration and methodology come from the 'QtAwesome' module, which does exactly this, but
is a little too big, complicated, and flexible for PyDM's needs.
"""

import json
import os
import sys
from typing import Optional

from qtpy import QtGui, QtWidgets
from qtpy.QtCore import QPoint, QRect, Qt
from qtpy.QtGui import QColor, QFont, QFontDatabase, QIcon, QIconEngine, QPainter, QPixmap

if sys.version_info[0] == 3:
    unichr = chr


class IconFont(object):
    """IconFont represents an icon font.  Users will generally want
    to use IconFont.icon() to get a QIcon object for the character they want."""

    __instance = None

    def __init__(self):
        if self.__initialized:
            return
        self.font_file = "fontawesome.otf"  # specify these relative to this file.
        self.charmap_file = "fontawesome-charmap.json"
        self.font_name = None
        self.char_map = {}
        self.loaded_fonts = {}
        self.__initialized = True

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(IconFont)
            cls.__instance.__initialized = False
        return cls.__instance

    def load_font(self, ttf_filename, charmap_filename):
        """
        Load font from ``ttf_filename`` with a mapping defined in
        ``charmap_filename``.
        """

        def hook(obj):
            result = {}
            for key in obj:
                result[key] = unichr(int(obj[key], 16))
            return result

        if self.char_map:
            return

        cache_key = ttf_filename + "|" + charmap_filename
        ttf_fname = os.path.join(os.path.dirname(os.path.realpath(__file__)), ttf_filename)
        font_id = QFontDatabase.addApplicationFont(ttf_fname)
        if font_id >= 0:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
        else:
            cache = self.loaded_fonts.get(cache_key, None)
            if cache is None:
                raise OSError("Could not load ttf file for icon font.")
            self.char_map = cache["char_map"]
            self.font_name = cache["font_name"]
            return

        self.font_name = font_families[0]

        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), charmap_filename)
        with open(filename, "r") as codes:
            self.char_map = json.load(codes, object_hook=hook)

        self.loaded_fonts[cache_key] = {
            "char_map": self.char_map,
            "font_name": self.font_name,
        }

    def get_char_for_name(self, name: str) -> str:
        """
        Get a character icon for the given name from the character map.

        Parameters
        ----------
        name : str
            The user-friendly icon name.

        Returns
        -------
        str
            The Qt-facing icon text to use with the font.
        """
        if name in self.char_map:
            return self.char_map[name]
        raise ValueError("Invalid icon name for font.")

    def _load_font_if_needed(self) -> bool:
        """
        Load the configured font if a QApplication is available
        and the font was not already loaded.

        Returns
        -------
        bool
            Readiness indicator - return True if the font has been loaded.
        """
        if QtWidgets.QApplication.instance() is None:
            return False

        if not self.char_map:
            self.load_font(self.font_file, self.charmap_file)

        # If it was loaded correctly, the char map will be populated:
        return bool(self.char_map)

    def font(self, size: int) -> Optional[QtGui.QFont]:
        """
        Load the font at a given pixel size.

        Returns
        -------
        QtGui.QFont or None
            The font, if available.  If a QApplication is not yet created,
            None will be returned.
        """
        if not self._load_font_if_needed():
            return None

        font = QFont(self.font_name)
        font.setPixelSize(int(size))
        return font

    def icon(self, name, color=None) -> Optional[QtGui.QIcon]:
        """
        Retrieve the icon given a name and color.

        Parameters
        ----------
        name : str
            The Icon string identifier.
            Icon strings can be found at: https://fontawesome.com/icons?d=gallery

        color : QColor, Optional
            The base color to use when constructing the Icon. Default is QColor(90, 90, 90).

        Returns
        -------
        QIcon
            The desired Icon.  ``None`` if a QApplication is not yet available.
        """
        if not self._load_font_if_needed():
            return None

        char = self.get_char_for_name(name)
        engine = CharIconEngine(self, char, color)
        return QIcon(engine)


class CharIconEngine(QIconEngine):
    """Subclass of QIconEngine that is designed to draw characters from icon fonts."""

    def __init__(self, icon_font, char, color=None):
        super().__init__()
        self.icon_font = icon_font
        self.char = char
        if color is None:
            self._base_color = QColor(90, 90, 90)
        else:
            self._base_color = color
        self._disabled_color = QColor.fromHslF(
            self._base_color.hueF(),
            self._base_color.saturationF(),
            max(min(self._base_color.lightnessF() + 0.25, 1.0), 0.0),
        )

    def paint(self, painter, rect, mode, state):
        painter.save()
        if mode == QIcon.Disabled:
            color = self._disabled_color
        else:
            color = self._base_color
        painter.setPen(color)
        scale_factor = 1.0
        draw_size = 0.875 * round(rect.height() * scale_factor)
        painter.setFont(self.icon_font.font(draw_size))
        painter.setOpacity(1.0)
        painter.drawText(rect, int(Qt.AlignCenter | Qt.AlignVCenter), self.char)
        painter.restore()

    def pixmap(self, size, mode, state):
        pm = QPixmap(size)
        pm.fill(Qt.transparent)
        self.paint(QPainter(pm), QRect(QPoint(0, 0), size), mode, state)
        return pm
