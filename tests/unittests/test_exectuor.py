import time
import unittest

from observer_toolkit.utils._executor import Executor


def mock_function(**kwargs):
    return kwargs


def initial_callback() -> None:
    pass


def timeout_initial_callback() -> None:
    time.sleep(20)


def error_initial_callback() -> None:
    raise Exception("error")


def wrong_initial_callback(wrong_parameter) -> None:
    pass


def execute_timeout_callback(**kwargs) -> None:
    time.sleep(20)


def execute_error_callback(**kwargs) -> None:
    raise Exception("error")


def execute_wrong_callback(wrong_parameter) -> None:
    pass


def execute_infinite_callback(**kwargs) -> None:
    while True:
        time.sleep(1)


class ExecutorTestCase(unittest.TestCase):

    def test_executor_property(self):
        """test case for executor property"""

    def test_executor_initial_callback(self):
        executor = Executor(execute_callback=mock_function, initial_callback=initial_callback)

        self.assertTrue(executor.is_alive())

    def test_executor_initial_callback_failed(self):
        with self.subTest('timeout'):
            with self.assertRaises(TimeoutError):
                Executor(
                    execute_callback=mock_function,
                    initial_callback=timeout_initial_callback,
                    initial_timeout=0.1)

        with self.subTest('error'):
            with self.assertRaises(Exception):
                Executor(
                    execute_callback=mock_function,
                    initial_callback=error_initial_callback,
                    initial_timeout=0.1)

        with self.subTest('wrong'):
            with self.assertRaises(AssertionError):
                Executor(
                    execute_callback=mock_function,
                    initial_callback=wrong_initial_callback,
                    initial_timeout=0.1)

    def test_executor_execute_callback(self):
        parameter = {'parameter': 'parameter_content'}

        executor = Executor(execute_callback=mock_function, )

        future = executor.submit(parameter)

        result = future.get_result()

        #
        result = mock_function(**parameter)

        self.assertEqual(parameter, Executor(execute_callback=mock_function, ).submit(parameter).get_result())

    def test_executor_execute_callback_failed(self):
        with self.subTest('timeout in future.get_result'):
            with self.assertRaises(AssertionError):
                Executor(execute_callback=execute_timeout_callback).submit({}).get_result(timeout=0.1)

        with self.subTest('timeout in executor'):
            with self.assertRaises(TimeoutError):
                Executor(execute_callback=execute_timeout_callback, execute_timeout=0.1).submit({}).get_result()

        with self.subTest('error'):
            with self.assertRaises(Exception):
                result = Executor(execute_callback=execute_error_callback).submit({}).get_result()

        with self.subTest('wrong parameter'):
            with self.assertRaises(AssertionError):
                Executor(execute_callback=execute_wrong_callback)

    def test_executor_performance(self):
        """test case for executor manager"""

        # empty
        executor = Executor(execute_callback=mock_function, )
        number = 32
        s = time.time()
        for i in range(number):
            item_s = time.time()
            future = executor.submit({})
            # print('future cost:', time.time() - item_s)

            r = future.get_result()
            print('total cost:', time.time() - item_s)

        print('cost:', time.time() - s)

    def test_todo(self):
        """TODO"""


if __name__ == '__main__':
    unittest.main()
