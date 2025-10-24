"""Batch run SPARK3D."""

import importlib.metadata

__version__ = importlib.metadata.version("spark3d_batch")
from pathlib import Path

from . import log_manager  # assuming your script is logging_setup.py

default_log_file = Path.home() / ".spark3dbatch.log"

log_manager.set_up_logging(
    package_name="spark3d_batch",
    console_log_output="stdout",
    console_log_level="INFO",
    console_log_color=True,
    console_log_line_template="%(color_on)s[%(levelname)-8s] [%(filename)-20s]%(color_off)s %(message)s",
    logfile_file=default_log_file,
    logfile_log_level="INFO",
    logfile_log_color=False,
    logfile_line_template="%(color_on)s[%(asctime)s] [%(levelname)-8s] [%(filename)-20s]%(color_off)s %(message)s",
)
