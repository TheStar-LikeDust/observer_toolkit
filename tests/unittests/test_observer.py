import unittest
from unittest.mock import MagicMock

from observer_toolkit import Observer, Step


class TestObserver(Observer):
    steps = [
        Step('step_1')
    ]


class TestObserver2(Observer):
    steps = [
        Step('step_1'),
        Step('step_2', dependency_actions=['step_1']),
    ]


def judge_callback(**kwargs):
    return True


def trigger_callback(**kwargs):
    kwargs.get('ob').mock()


class TestObserver3(Observer):
    steps = [
        Step('step_1'),
        Step('step_2', dependency_actions=['step_1']),
    ]

    judge_callback = judge_callback
    trigger_callback = trigger_callback


class ObserverTestCase(unittest.TestCase):

    def test_observer_initial(self):
        observer = TestObserver()

        self.assertEqual(observer.name, 'TestObserver')

        with self.subTest('property : plan'):
            self.assertEqual(len(observer.plan), 1)

            # for _ in observer.plan.walk():
            #     print(_)

            for _ in TestObserver2().plan.walk():
                print(_)

    def test_judge(self):
        observer = TestObserver()
        mock = MagicMock()
        observer.judge_callback = mock

        [observer.judge({}) for _ in range(10)]

        self.assertEqual(observer._judge_result_deque.get_rate(), 0)

        observer.judge({'step_1': 'content'})
        mock.assert_called_once()

    def test_trigger(self):
        observer = TestObserver()
        mock = MagicMock()

        observer.judge_callback = lambda **k: True
        observer.trigger_callback = mock

        [observer.judge({}) for _ in range(10)]
        observer.trigger({})

        mock.assert_not_called()

        [observer.judge({'step_1': 'content'}) for _ in range(10)]
        observer.trigger({})

        mock.assert_called_once()

    def test_observer_manager(self):
        observer = TestObserver3()
        mock = MagicMock()
        observer.mock = mock

        [
            observer.do_action({
                'step_1': 'content',
                'step_2': 'content',
            })
            for _ in range(6)
        ]

        mock.assert_called_once()

        # ready

        observer.ready_status = False

        [
            observer.do_action({
                'step_1': 'content',
                'step_2': 'content',
            })
            for _ in range(15)
        ]

        mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
