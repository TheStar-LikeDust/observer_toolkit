import unittest

from observer_toolkit.utils import ExecutorManager
from observer_toolkit import get_action


class ObserverManagerActionTestCase(unittest.TestCase):

    def test_observer_manager(self):
        executor_manager = ExecutorManager()


if __name__ == '__main__':
    unittest.main()
