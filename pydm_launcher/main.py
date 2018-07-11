import sys
import argparse
from pydm import PyDMApplication
import json
import logging


def main():
    parser = argparse.ArgumentParser(description="Python Display Manager")
    parser.add_argument(
        'displayfile',
        help='A PyDM file to display.' +
             '    Can be either a Qt .ui file, or a Python file.',
        nargs='?',
        default=None
        )
    parser.add_argument(
        'stylesheet',
        help='Provide the full path to the CSS stylesheet file, which must contain the appearances (styles) to be'
             'applied to specific Qt/PyDM widget types.',
        nargs='*',
        default=None
        )
    parser.add_argument(
        '--perfmon',
        action='store_true',
        help='Enable performance monitoring,' +
             ' and print CPU usage to the terminal.'
        )
    parser.add_argument(
        '--hide-nav-bar',
        action='store_true',
        help='Start PyDM with the navigation bar hidden.'
        )
    parser.add_argument(
        '--hide-menu-bar',
        action='store_true',
        help='Start PyDM with the menu bar hidden.'
        )
    parser.add_argument(
        '--hide-status-bar',
        action='store_true',
        help='Start PyDM with the status bar hidden.'
        )
    parser.add_argument(
        '--read-only',
        action='store_true',
        help='Start PyDM in a Read-Only mode.'
        )
    parser.add_argument(
        '--log_level',
        help='Configure level of log display',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO'
        )
    parser.add_argument(
        '-m', '--macro',
        help='Specify macro replacements to use, in JSON object format.' +
             '    Reminder: JSON requires double quotes for strings, ' +
             'so you should wrap this whole argument in single quotes.' +
             '  Example: -m \'{"sector": "LI25", "facility": "LCLS"}\'' +
             '--or-- specify macro replacements as KEY=value pairs ' +
             ' using a comma as delimiter  If you want to uses spaces ' +
             ' after the delimiters or around the = signs, ' +
             ' wrap the entire set with quotes ' +
             '  Example: -m "sector = LI25, facility=LCLS"'
        )
    parser.add_argument(
        'display_args',
        help='Arguments to be passed to the PyDM client application' +
             ' (which is a QApplication subclass).',
        nargs=argparse.REMAINDER,
        default=None
        )

    pydm_args = parser.parse_args()
    macros = None
    if pydm_args.macro is not None:
        try:
            macros = json.loads(pydm_args.macro)
        except ValueError:
            if pydm_args.macro.find("=") < 0:
                raise ValueError("Could not parse macro argument as JSON.")
            macros = {}
            for pair in pydm_args.macro.split(","):
                key, value = pair.strip().split("=")
                macros[key.strip()] = value.strip()

    logger = logging.getLogger('')
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)-8s] - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if pydm_args.log_level:
        logger.setLevel(pydm_args.log_level)
        handler.setLevel(pydm_args.log_level)

    app = PyDMApplication(
        ui_file=pydm_args.displayfile,
        command_line_args=pydm_args.display_args,
        perfmon=pydm_args.perfmon,
        hide_nav_bar=pydm_args.hide_nav_bar,
        hide_menu_bar=pydm_args.hide_menu_bar,
        hide_status_bar=pydm_args.hide_status_bar,
        read_only=pydm_args.read_only,
        macros=macros,
        stylesheet_path=pydm_args.stylesheet[1] if pydm_args.stylesheet and len(pydm_args.stylesheet) == 2 else None
        )

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
