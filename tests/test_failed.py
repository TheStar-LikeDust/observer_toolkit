# -*- coding: utf-8 -*-
"""
"""
from types import TracebackType

from observer_toolkit import smart_launch, smart_run
from observer_toolkit.utils._executor import Executor


class MyException(Exception):

    def with_traceback(self, tb):
        return None


def _executor_failed_callback(**kwargs):
    0 / 0


def executor_failed():
    result = Executor(execute_callback=_executor_failed_callback).submit({}).get_result(timeout=1000)


if __name__ == '__main__':
    raise MyException()
