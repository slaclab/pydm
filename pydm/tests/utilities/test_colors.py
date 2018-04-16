import pytest

from ...utilities import colors


def test_read_file():
    assert(colors.svg_color_to_hex_map is not None)
    assert (colors.hex_to_svg_color_map is not None)


def test_svg_color_from_hex():
    svg = colors.svg_color_from_hex('#000000', hex_on_fail=False)
    assert (svg == 'black')
    svg = colors.svg_color_from_hex('#000000', hex_on_fail=True)
    assert (svg == 'black')

    with pytest.raises(KeyError):
        colors.svg_color_from_hex('#XXXXXXX', hex_on_fail=False)
    svg = colors.svg_color_from_hex('#XXXXXXX', hex_on_fail=True)
    assert(svg == '#XXXXXXX')


def test_hex_from_svg_color():
    hex = colors.hex_from_svg_color('black')
    assert (hex == '#000000')

    with pytest.raises(KeyError):
        colors.hex_from_svg_color('invalid_color')
