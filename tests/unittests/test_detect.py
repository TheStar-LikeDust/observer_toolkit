import unittest

from observer_toolkit.utils._detect import detect_action, get_action


class DetectTestCase(unittest.TestCase):

    def test_detect_action(self):
        actions = detect_action('tests.unittests.mock_packages.mock_actions')

        self.assertEqual(len(list(actions)), 5)
        sub = get_action('sub')


        print(sub.step_task_expend_function)

    def test_detect_error_action(self):
        with self.assertRaises(Exception) as e:
            detect_action('tests.unittests.mock_packages.mock_error_actions')


if __name__ == '__main__':
    unittest.main()
