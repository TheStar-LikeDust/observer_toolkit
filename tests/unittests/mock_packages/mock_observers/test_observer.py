# coding: utf-8
from observer_toolkit import Observer, Step


def judge(**kwargs):
    pass
    # print('here is judge')
    return True


def trigger(**kwargs):
    # print('trigger')
    pass


class MockObserver(Observer):
    steps = [
        # Step('normal_action'),
        Step('iter'),
        Step('sub', ['iter']),
    ]

    judge_callback = judge

    trigger_callback = trigger
