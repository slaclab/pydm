import pickle
import os
import itertools

current_dir = os.path.dirname(os.path.realpath(__file__))

svg_color_to_hex_map = None
hex_to_svg_color_map = None
with open(os.path.join(current_dir, 'hex2color.pkl')) as f:
  hex_to_svg_color_map = pickle.load(f)
with open(os.path.join(current_dir, 'color2hex.pkl')) as f:
  svg_color_to_hex_map = pickle.load(f)
  
def svg_color_from_hex(hex_string):
  return hex_to_svg_color_map[str(hex_string).lower()]
  
def hex_from_svg_color(color_string):
  return svg_color_to_hex_map[str(hex_string).lower()]

default_colors = ['white', 'red', 'dodgerblue', 'forestgreen', 'yellow', 'fuchsia', 'turquoise', 'deeppink', 'lime', 'orange', 'whitesmoke', 'beige', 'purple', 'teal', 'darksalmon', 'brown']