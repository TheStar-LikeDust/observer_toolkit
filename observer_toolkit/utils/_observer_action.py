# coding: utf-8
from typing import Optional

from observer_toolkit import Observer

GLOBAL_OBSERVER: Optional[Observer] = None


def initial_observer_wrapper(observer_class):
    def _inner_initial_observer():
        global GLOBAL_OBSERVER
        GLOBAL_OBSERVER = observer_class()

    return _inner_initial_observer


def execute_observer(**kwargs):
    return GLOBAL_OBSERVER.do_action(kwargs)
