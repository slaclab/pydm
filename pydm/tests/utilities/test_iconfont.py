import pytest
from ...utilities import iconfont
from qtpy import QtGui, QtCore


def test_icon_font_constructor(qtbot):
    icon_f = iconfont.IconFont()
    icon_f2 = iconfont.IconFont()
    assert (icon_f is icon_f2)


def test_icon_font_load_font(qtbot):
    icon_f = iconfont.IconFont()
    with pytest.raises(OSError):
        icon_f.char_map = None
        icon_f.load_font('foo', icon_f.charmap_file)
    with pytest.raises(OSError):
        icon_f.char_map = None
        icon_f.load_font(icon_f.charmap_file, 'foo')
    icon_f.load_font(icon_f.font_file, icon_f.charmap_file)
    assert (icon_f.char_map is not None)


def test_icon_font_get_char_for_name(qtbot):
    icon_f = iconfont.IconFont()
    c = icon_f.get_char_for_name('cogs')
    assert (c == u'\uf085')

    with pytest.raises(ValueError):
        icon_f.get_char_for_name('foo')


def test_icon_font_font(qtbot):
    icon_f = iconfont.IconFont()
    f = icon_f.font(12)
    assert(f.family() == icon_f.font_name)
    assert(f.pixelSize() == 12)


def test_icon_font_icon(qtbot):
    icon_f = iconfont.IconFont()
    ico = icon_f.icon('cogs', color=None)
    ico1 = icon_f.icon('cogs', color=QtGui.QColor(255, 0, 0))
    with pytest.raises(ValueError):
        ico_invalid = icon_f.icon('foo', color=None)


def test_char_icon_engine(qtbot):
    engine = iconfont.CharIconEngine(iconfont.IconFont(), 'cogs', color=None)
    pm = engine.pixmap(QtCore.QSize(32, 32), mode=QtGui.QIcon.Normal, state=QtGui.QIcon.On)
    pm = engine.pixmap(QtCore.QSize(32, 32), mode=QtGui.QIcon.Disabled, state=QtGui.QIcon.On)