import sys
import traceback
from types import TracebackType
from typing import Any, Type

from .base import BaseException as ScseToolkitBaseException


class NoTracebackException(ScseToolkitBaseException):
    __suppress_traceback__: bool = True


original_excepthook = sys.excepthook


def no_traceback_excepthook(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,  # noqa
) -> Any:
    if getattr(exc_value, "__suppress_traceback__", False) is True:
        traceback.print_exception(exc_type, exc_value, None)
    else:
        original_excepthook(exc_type, exc_value, exc_traceback)


sys.excepthook = no_traceback_excepthook
