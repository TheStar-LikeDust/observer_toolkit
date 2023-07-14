import unittest

from observer_toolkit.step import get_action

from observer_toolkit import Step, StepPlan, detect_action, smart_launch, smart_run
from observer_toolkit.utils import ExecutorManager, GLOBAL_EXECUTOR_MANAGER


class ExecutorManagerTestCase(unittest.TestCase):

    def test_executor_manager(self):
        """Test that the ExecutorManager class works as expected."""

        manager = ExecutorManager()

        with self.subTest('arguments: execute timeout'):
            self.assertEqual(manager.execute_timeout, 5)

        with self.subTest('arguments: initial timeout'):
            self.assertEqual(manager.initial_timeout, 5)

        with self.subTest('properties: mapper'):
            self.assertEqual(manager.executor_mapper, dict())

    def test_register_action(self):
        """Test that the register_action method works as expected."""



if __name__ == '__main__':
    unittest.main()
