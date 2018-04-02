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

def init():
    global _log_file
    global _log_dir
    global _stdout
    global _stderr

    logging.basicConfig(format=_basic_format)
    logger.setLevel(logging.DEBUG)
