# coding: utf-8
from observer_toolkit import Observer, Step


def judge(**kwargs):
    pass


class PerformanceObserver(Observer):
    steps = [
        Step('performance_iter'),
        Step('performance_sub', ['performance_iter']),
    ]

    judge_callback = judge
