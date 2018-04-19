import pickle
import os

current_dir = os.path.dirname(os.path.realpath(__file__))

svg_color_to_hex_map = None
hex_to_svg_color_map = None
with open(os.path.join(current_dir, 'hex2color.pkl'), 'rb') as f:
    hex_to_svg_color_map = pickle.load(f)
with open(os.path.join(current_dir, 'color2hex.pkl'), 'rb') as f:
    svg_color_to_hex_map = pickle.load(f)


def svg_color_from_hex(hex_string, hex_on_fail=False):
    """
    Returns the SVG color based on its HEX equivalent.

    Parameters
    ----------
    hex_string: str
        The color code in hex. E.g. #000000

    hex_on_fail: bool, Optional
        Whether or not to return the `hex_string` when an invalid color is submitted.
        Default is False.

    Returns
    -------
    str
        The SVG color string.
    """
    if not hex_on_fail:
        return hex_to_svg_color_map[str(hex_string).lower()]
    try:
        return hex_to_svg_color_map[str(hex_string).lower()]
    except KeyError:
        return hex_string


def hex_from_svg_color(color_string):
    """
    Returns the HEX color based on its SVG equivalent.

    Parameters
    ----------
    color_string: str
        The SVG color string. E.g. black

    Returns
    -------
    str
        The HEX color string.
    """
    return svg_color_to_hex_map[str(color_string).lower()]


default_colors = ['white', 'red', 'dodgerblue', 'forestgreen', 'yellow',
                  'fuchsia', 'turquoise', 'deeppink', 'lime', 'orange',
                  'whitesmoke', 'beige', 'purple', 'teal', 'darksalmon',
                  'brown']
