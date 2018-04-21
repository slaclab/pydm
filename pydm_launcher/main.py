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
        default=logging.INFO
        )
    parser.add_argument(
        '-m', '--macro',
        help='Specify macro replacements to use, in JSON object format.' +
             '    Reminder: JSON requires double quotes for strings, ' +
             'so you should wrap this whole argument in single quotes.' +
             '  Example: -m \'{"sector": "LI25", "facility": "LCLS"}\''
        )
    parser.add_argument(
        'display_args',
        help='Arguments to be passed to the PyDM client application' +
             ' (which is a QApplication subclass).',
        nargs=argparse.REMAINDER
        )
    pydm_args = parser.parse_args()
    macros = None
    if pydm_args.macro is not None:
        try:
            macros = json.loads(pydm_args.macro)
        except ValueError:
            raise ValueError("Could not parse macro argument as JSON.")

    logging.basicConfig(
        level=pydm_args.log_level,
        format='[%(asctime)s] - %(message)s'
        )

    app = PyDMApplication(
        ui_file=pydm_args.displayfile,
        command_line_args=pydm_args.display_args,
        perfmon=pydm_args.perfmon,
        hide_nav_bar=pydm_args.hide_nav_bar,
        hide_menu_bar=pydm_args.hide_menu_bar,
        hide_status_bar=pydm_args.hide_status_bar,
        read_only=pydm_args.read_only,
        macros=macros
        )

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
