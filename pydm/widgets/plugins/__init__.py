import sys
from os import path

widget_path = path.join(path.dirname(path.abspath(__file__)),'../')
sys.insert(0,widget_path)

