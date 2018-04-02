#coding: utf-8

import logging

import os
import sys
import shutil


_basic_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
_console_format = '%(message)s'
_stdout = None
_stderr = None
_log_file = None
_log_dir = None

# Global logging
logger = logging.getLogger("pyDM Logger")


class InfoDebugFilter(logging.Filter):
    """
    Debug and Info filter for logging
    """
    def filter(self, record):
        """
        Log debug and info entries.
        :param record:
        :return:
        """
        return record.levelno in (logging.DEBUG, logging.INFO)


def prepare_logging(log_dir, verbose_mode=True):
    global _log_file
    global _log_dir
    global _stdout
    global _stderr

    if not log_dir:
        if not


def set_logging_params(log_dir, verbose, terse):
    """
    We have more logging settings discovered in cli arguments.
    Set the logging params.
    """

    global _log_file
    global _log_dir
    global _stdout
    global _stderr

    old_log_to_close = None

    if not log_dir:
        if not _log_file:
            _log_dir = utils.base.create_temp_dir()
        log_dir = _log_dir
    else:
        if not os.access(log_dir, os.W_OK):
            raise Exception(_("Passed log directory %(dir)s "
                              "is not writeable.") % dict(dir=log_dir))

        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        if _log_file:
            bkp_file = os.path.join(
                log_dir, "{}-cli-installer.log.bak".format(ic.get_product_short_name().lower()))
            print("Updating log file location, copying '%(old)s' to desired "
                  "location as a backup: '%(bkp)s'"
                  % {"old": _log_file, "bkp": bkp_file})

            # copy old log file to log_dir
            shutil.copy(_log_file, bkp_file)
            old_log_to_close = _log_file

    _log_file = os.path.join(
        log_dir, "{}-cli-installer.log".format(ic.get_product_short_name().lower()))

    # Reset basic logging for root logger so we can register new handlers
    for handler in logging.root.handlers[:]:
        handler.close()
        logging.root.removeHandler(handler)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    file_handler = logging.FileHandler(_log_file)
    file_handler.setFormatter(logging.Formatter(_basic_format))
    file_handler.setLevel(cli_logging.tracelogger.TRACE)

    _stderr.setLevel(logging.WARNING)
    _stdout.setLevel(logging.INFO)

    # Provide info about log file location on stdout
    # print "Log file location: ", _log_file

    if verbose:
        _stdout.setLevel(logging.DEBUG)
    elif terse:
        _stdout.setLevel(logging.WARNING)

    for log_handler in (_stdout, _stderr, file_handler):
        if log_handler:
            logger.addHandler(log_handler)

    logging.captureWarnings(True)
    logging.getLogger('py.warnings').addHandler(file_handler)

    # after modifying the logging configuration, try to close and remove the
    # old log file if any. On windows, removing an opened file will cause
    # exception, so we try to remove the file after we re-configure the handler
    if old_log_to_close:
        try:
            os.remove(old_log_to_close)
        except OSError as e:
            print("Failed to remove old log file: '%(old_log)s' because %(e)s, "
                  "this does not affect the execution in any ways"
                  % {"old_log": old_log_to_close, "e": e})

    return log_dir, _log_file