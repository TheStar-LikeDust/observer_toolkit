import unittest

from observer_toolkit.step import clear_registered_actions, get_action

MOCK_ACTIONS = 'tests.unittests.mock_packages.mock_actions'


class StepTestCase(unittest.TestCase):

    def setUp(self) -> None:
        clear_registered_actions()

    def test_action(self):
        action = get_action('action')
        self.assertEqual(action.name, 'action')

        # hashable
        hash(action)

    def test_action_singleton(self):
        """Action is a singleton"""

        action_1 = get_action('singleton')
        action_2 = get_action('singleton')

        self.assertEqual(action_1, action_2)
        self.assertIs(action_1, action_2)

    def test_action_singleton_update_property(self):
        """Test that the singleton action is updated when a new action is registered with the same name"""
        from observer_toolkit.step import Action

        action_function = lambda **k: {}

        action_update_1 = Action(name='update_testcase')
        action_update_2 = Action(name='update_testcase', action_function=action_function)

        self.assertIs(action_update_1, action_update_2)
        self.assertIs(action_update_1.action_function, action_update_2.action_function)
        self.assertIs(action_update_2.action_function, action_function)


if __name__ == '__main__':
    unittest.main()
