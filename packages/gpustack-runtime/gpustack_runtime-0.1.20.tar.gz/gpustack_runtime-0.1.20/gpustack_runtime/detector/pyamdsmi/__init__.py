# Bridge amdsmi module to avoid import errors when amdsmi is not installed
# This module raises an exception when amdsmi_init is called
# and does nothing when amdsmi_shut_down is called.
from __future__ import annotations

import contextlib
import os
from pathlib import Path

try:
    with contextlib.redirect_stdout(Path(os.devnull).open("w")):
        from amdsmi import *
except (ImportError, KeyError, OSError):

    class AmdSmiException(Exception):
        pass

    def amdsmi_init(*_):
        msg = (
            "amdsmi module is not installed, please install it via 'pip install amdsmi'"
        )
        raise AmdSmiException(msg)

    def amdsmi_get_processor_handles():
        return []

    def amdsmi_shut_down():
        pass
