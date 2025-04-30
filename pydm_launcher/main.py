import argparse
import cProfile
import logging
import os
import pstats
import sys
import faulthandler
from qtpy import QtCore, QtGui


def main():
    logger = logging.getLogger("")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)-8s] - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel("INFO")
    handler.setLevel("INFO")

    from pydm.utilities import setup_renderer

    setup_renderer()

    try:
        """
        We must import QtWebEngineWidgets before creating a QApplication
        otherwise we get the following error if someone adds a WebView at Designer:
        ImportError: QtWebEngineWidgets must be imported before a QCoreApplication instance is created
        """
        from qtpy import QtWebEngineWidgets  # noqa: F401
    except ImportError:
        logger.debug("QtWebEngine is not supported.")

    import pydm
    from pydm.utilities.macro import parse_macro_string

    parser = argparse.ArgumentParser(description="Python Display Manager")
    parser.add_argument(
        "displayfile",
        help="A PyDM file to display." + "    Can be either a Qt .ui file, or a Python file.",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "-r",
        "--recurse",
        action="store_true",
        help="Recursively search for the provided displayfile in the current working directory and subfolders",
    )
    parser.add_argument(
        "--homefile", help="Path to a PyDM file to return to when the home button is clicked in the navigation bar"
    )
    parser.add_argument(
        "--perfmon",
        action="store_true",
        help="Enable performance monitoring, and print CPU usage to the terminal.",
    )
    parser.add_argument("--profile", action="store_true", help="Enable cProfile function profiling, printing on exit.")
    parser.add_argument("--faulthandler", action="store_true", help="Enable faulthandler to trace segmentation faults.")
    parser.add_argument("--hide-nav-bar", action="store_true", help="Start PyDM with the navigation bar hidden.")
    parser.add_argument("--hide-menu-bar", action="store_true", help="Start PyDM with the menu bar hidden.")
    parser.add_argument("--hide-status-bar", action="store_true", help="Start PyDM with the status bar hidden.")
    parser.add_argument("--fullscreen", action="store_true", help="Start PyDM in full screen mode.")
    parser.add_argument("--read-only", action="store_true", help="Start PyDM in a Read-Only mode.")
    parser.add_argument(
        "--log_level",
        help="Configure level of log display",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="PyDM {version}".format(version=pydm.__version__),
        help="Show PyDM's version number and exit.",
    )
    parser.add_argument(
        "-m",
        "--macro",
        help="Specify macro replacements to use, in JSON object format."
        + "    Reminder: JSON requires double quotes for strings, "
        + "so you should wrap this whole argument in single quotes."
        + '  Example: -m \'{"sector": "LI25", "facility": "LCLS"}\''
        + "--or-- specify macro replacements as KEY=value pairs "
        + " using a comma as delimiter  If you want to uses spaces "
        + " after the delimiters or around the = signs, "
        + " wrap the entire set with quotes "
        + '  Example: -m "sector = LI25, facility=LCLS"',
    )
    parser.add_argument(
        "--stylesheet",
        help="Specify the full path to a CSS stylesheet file, which"
        + " can be used to customize the appearance of PyDM and"
        + " Qt widgets.",
        default=None,
    )
    parser.add_argument(
        "display_args",
        help="Arguments to be passed to the PyDM client application" + " (which is a QApplication subclass).",
        nargs=argparse.REMAINDER,
        default=None,
    )

    pydm_args = parser.parse_args()
    if pydm_args.profile:
        profile = cProfile.Profile()
        profile.enable()

    if pydm_args.faulthandler:
        faulthandler.enable()

    macros = None
    if pydm_args.macro is not None:
        macros = parse_macro_string(pydm_args.macro)

    if pydm_args.log_level:
        logger.setLevel(pydm_args.log_level)
        handler.setLevel(pydm_args.log_level)

    app = pydm.PyDMApplication(
        ui_file=pydm_args.displayfile,
        command_line_args=pydm_args.display_args,
        perfmon=pydm_args.perfmon,
        hide_nav_bar=pydm_args.hide_nav_bar,
        hide_menu_bar=pydm_args.hide_menu_bar,
        hide_status_bar=pydm_args.hide_status_bar,
        fullscreen=pydm_args.fullscreen,
        read_only=pydm_args.read_only,
        macros=macros,
        recursive_display_search=pydm_args.recurse,
        stylesheet_path=pydm_args.stylesheet,
        home_file=pydm_args.homefile,
    )

    base_path = os.path.dirname(os.path.realpath(__file__))
    icon_path_mask = os.path.join(base_path, "icons", "pydm_{}.png")

    app_icon = QtGui.QIcon()
    app_icon.addFile(icon_path_mask.format(16), QtCore.QSize(16, 16))
    app_icon.addFile(icon_path_mask.format(24), QtCore.QSize(24, 24))
    app_icon.addFile(icon_path_mask.format(32), QtCore.QSize(32, 32))
    app_icon.addFile(icon_path_mask.format(64), QtCore.QSize(64, 64))
    app_icon.addFile(icon_path_mask.format(128), QtCore.QSize(128, 128))
    app_icon.addFile(icon_path_mask.format(256), QtCore.QSize(256, 256))

    app.setWindowIcon(app_icon)
    app.setApplicationName("PyDM")

    pydm.utilities.shortcuts.install_connection_inspector(parent=app.main_window)

    exit_code = app.exec_()

    if pydm_args.profile:
        profile.disable()
        stats = pstats.Stats(
            profile,
            stream=sys.stdout,
        ).sort_stats(pstats.SortKey.CUMULATIVE)
        stats.print_stats()

    if pydm_args.faulthandler:
        faulthandler.disable()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
