# Module Name: helpers/handlers.py
# Description: This modul contains trace handler class.
# Author: (wattleflow@outlook.com)
# Copyright: (c) 2022-2025 WattleFlow
# License: Apache 2 Licence

"""
This module implements a trace handler for enhanced logging within the
Wattleflow framework. It extends the standard logging handler to include
detailed stack traces for captured exceptions, improving error visibility
and debugging efficiency.
"""

import logging
import traceback


class TraceHandler(logging.StreamHandler):
    def emit(self, record):
        if isinstance(record, BaseException):
            error = record
        else:
            error = getattr(record, "error", None)

        if error and isinstance(error, Exception):
            record.msg += "\n" + "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )

        super().emit(record)
