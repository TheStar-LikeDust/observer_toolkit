import threading
import time
import unittest
import queue

from observer_toolkit.utils._executor import SharedValue, send_parameter, send_result, ExecutorFuture, ExecutorResult


class ExecutorTestCase(unittest.TestCase):

    def test_shared_value(self):
        sv = SharedValue()

        obj = {
            'name': 'name',
            'age': 123,
        }

        sv.set_object(obj)
        assert sv.get_object() == obj

    def test_send_parameter(self):
        q = queue.Queue()
        sv = SharedValue()
        parameter_ready_event = threading.Event()
        parameter_received_event = threading.Event()

        # put some items and start thread.
        [q.put(i) for i in range(10)]
        threading.Thread(target=send_parameter, args=(q, sv, parameter_ready_event, parameter_received_event),
                         daemon=True).start()

        # ----- cycle start -----
        parameter_ready_event.wait()
        parameter_ready_event.clear()

        self.assertEqual(sv.get_object(), 0)
        self.assertEqual(q.qsize(), 9)

        parameter_received_event.set()
        # ----- cycle end -----

        for i in range(1, 10):
            parameter_ready_event.wait()
            parameter_ready_event.clear()

            self.assertEqual(sv.get_object(), i)
            self.assertEqual(q.qsize(), 9 - i)

            parameter_received_event.set()

    def test_send_result_in_executor(self):
        q = queue.Queue()
        sv = SharedValue()
        result_ready_event = threading.Event()
        result_received_event = threading.Event()

        # create futures and start thread.
        futures = [ExecutorFuture() for _ in range(10)]
        [q.put(future) for future in futures]
        threading.Thread(target=send_result, args=(q, sv, result_ready_event, result_received_event),
                         daemon=True).start()

        # ----- cycle start -----

        # in sub process (executor)
        sv.set_object(ExecutorResult(result=100 + 0))

        result_ready_event.set()

        result_received_event.wait()
        result_received_event.clear()

        # in other thread.
        self.assertEqual(futures[0].get_result(), 100 + 0)
        self.assertTrue(futures[0].finished)

        # ----- cycle end -----

        for i in range(1, 10):
            sv.set_object(ExecutorResult(result=100 + i))

            result_ready_event.set()

            result_received_event.wait()
            result_received_event.clear()

            # in other thread.
            self.assertEqual(futures[i].get_result(), 100 + i)
            self.assertTrue(futures[i].finished)

        self.assertTrue(all([future.finished for future in futures]))

    def test_send_result_in_main(self):
        q = queue.Queue()
        sv = SharedValue()
        result_ready_event = threading.Event()
        result_received_event = threading.Event()

        # create futures and start thread.
        futures = [ExecutorFuture() for _ in range(10)]
        [q.put(future) for future in futures]
        threading.Thread(target=send_result, args=(q, sv, result_ready_event, result_received_event),
                         daemon=True).start()

        # simulate executor
        def executor_simulator():
            for i in range(100):
                sv.set_object(i + 100)
                result_ready_event.set()
                result_received_event.wait()
                result_received_event.clear()

        threading.Thread(target=executor_simulator, daemon=True).start()

        time.sleep(0.001)
        self.assertTrue(all([future.finished for future in futures]))




if __name__ == '__main__':
    unittest.main()
