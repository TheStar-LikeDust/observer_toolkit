# coding : utf-8
import ctypes
import queue
import signal
import sys
import threading
import multiprocessing

import pickle
import _pickle as cPickle
import marshal
import time
import traceback

from inspect import signature, Parameter
from typing import Iterable, Any, Callable, Union, Dict, List, NamedTuple
from threading import Thread
from multiprocessing import Array, Value, Barrier, Process, RawArray

from observer_toolkit.step import Action, get_registered_actions

DEFAULT_INITIAL_CALLBACK = lambda: None
DEFAULT_EXECUTE_CALLBACK = lambda **kwargs: kwargs
DEFAULT_FINAL_CALLBACK = lambda: None

DEFAULT_SHARED_MEMORY_SIZE = 64 * 1024 * 1024


class SharedValue(object):
    """save Python object into shared memory."""

    def __init__(self, value=None, size: int = None):

        size = size or DEFAULT_SHARED_MEMORY_SIZE

        if value is not None:
            self._array = value
        else:
            self._array = RawArray('c', size)

        # self._value = Value('i', 0)
        self.size = size

    def _set(self, bytes_data: bytes) -> None:
        """set bytes_data into memory(bytes).

        The head 4 bytes is the length of bytes_data and the rest is bytes_data.
        """
        # slice cost slow when set object

        length = len(bytes_data)
        assert length <= self.size, f'bytes_data length {length} > {self.size}.'

        # length_bytes = length.to_bytes(4, 'big')
        # self._value.value = length
        self._array.value = bytes_data

    def _get(self) -> bytes:
        """get bytes_data from memory(bytes).

        Load the head 4 bytes as the length of bytes_data and slice the rest as bytes_data.
        """
        # slice cost slow when set object

        # length = int.from_bytes(self._array[:4], 'big')
        # return bytes(self._array[4:length + 4])

        # return self._array.raw[:int(self._value.value)]
        # TODO: wtf it works
        # https://stackoverflow.com/questions/37705974/why-are-multiprocessing-sharedctypes-assignments-so-slow
        # https://stackoverflow.com/questions/47380366/dramatic-slow-down-using-multiprocess-and-numpy-in-python
        return memoryview(self._array)

    def set_object(self, obj) -> None:
        if isinstance(obj, bytes):
            self._set(obj)
        else:
            self._set(pickle.dumps(obj))

    def get_object(self):
        bytes_data = self._get()
        obj = pickle.loads(bytes_data)
        return obj


class ExecutorResult(NamedTuple):
    """Result from Executor."""
    result: Any = None
    exception: Exception = None
    start_time: float = 0
    end_time: float = 0


class ExecutorFuture(object):
    _result = ExecutorResult
    """Result from Executor."""
    _event = None
    """Event to notify the result is ready."""

    @property
    def finished(self):
        return self._event.is_set()

    def __init__(self):
        self._result = None
        self._event = threading.Event()

        self._name = None

    def get_result(self, timeout: int = None, auto_raise: bool = True, executor_result: bool = False) -> Any:
        assert self._event.wait(timeout=timeout), f'ExecutorFuture timeout. name {self._name}'

        if auto_raise and self._result.exception is not None:
            # TODO
            raise self._result.exception

        if executor_result:
            return self._result
        else:
            return self._result.result

    def set_result(self, result: Any) -> None:
        self._result = result
        self._event.set()


def send_parameter(
        parameter_queue: queue.Queue,
        shared_value: SharedValue,
        parameter_ready_event: multiprocessing.Event,
        parameter_received_event: multiprocessing.Event,
):
    while True:
        # get parameter and save it into shared memory
        parameter = parameter_queue.get()
        shared_value.set_object(parameter)

        # notify executor the parameter is ready.
        parameter_ready_event.set()

        # wait for executor has received the parameter.
        parameter_received_event.wait()
        parameter_received_event.clear()


def send_result(
        future_queue: """queue.Queue[ExecutorFuture]""",
        shared_value: SharedValue,
        result_ready_event: multiprocessing.Event,
        result_received_event: multiprocessing.Event
):
    while True:
        # wait for executor has finished the task.
        result_ready_event.wait()
        result_ready_event.clear()

        # get result from shared memory and set it into future.
        result = shared_value.get_object()
        future = future_queue.get()
        future.set_result(result)

        # notify executor the result is received.
        result_received_event.set()


def execute_thread_callback(
        execute_callback: Callable[[Any], Any],
        execute_thread_parameter_queue: queue.Queue,
        execute_thread_result_queue: queue.Queue,
):
    while True:
        parameter = execute_thread_parameter_queue.get()
        try:
            result = execute_callback(**parameter)
        except Exception as e:
            # TODO: patch exception
            exc_type, exc_value, exc_traceback = sys.exc_info()

            # remove current frame
            exc_traceback = exc_traceback.tb_next
            traceback_content = ''.join(traceback.format_tb(exc_traceback))

            result = Exception(f'''<{exc_type.__name__}> It's msg "{exc_value}" and traceback:\n{traceback_content}''')
        execute_thread_result_queue.put(result)
        execute_thread_parameter_queue.task_done()


class Executor(Process):
    # properties in sub process by inheritance
    execute_timeout: Union[int, float]

    _parameter_shared_value: SharedValue
    _result_shared_value: SharedValue

    _initial_callback: Callable[[], Any]
    _execute_callback: Callable[[Any], Any]

    # events
    _parameter_ready_event: multiprocessing.Event
    _parameter_received_event: multiprocessing.Event
    _result_ready_event: multiprocessing.Event
    _result_received_event: multiprocessing.Event

    # queue in main process
    parameter_queue: queue.Queue
    future_queue: """queue.Queue[ExecutorFuture]"""

    # support threads
    _send_parameter_thread: Thread = None
    _send_result_thread: Thread = None

    def __init__(self,

                 execute_callback: Callable[[Any], Any],

                 initial_callback: Callable[[], Any] = DEFAULT_INITIAL_CALLBACK,
                 final_callback: Callable[[], Any] = DEFAULT_FINAL_CALLBACK,

                 initial_timeout: Union[int, float] = 10,
                 execute_timeout: Union[int, float] = 10,
                 name=None,
                 ):
        # properties in sub process by inheritance
        self._parameter_shared_value = SharedValue()
        self._result_shared_value = SharedValue()

        self._parameter_ready_event = multiprocessing.Event()
        self._parameter_received_event = multiprocessing.Event()
        self._result_ready_event = multiprocessing.Event()
        self._result_received_event = multiprocessing.Event()

        self._execute_callback = execute_callback
        self._initial_callback = initial_callback
        self._final_callback = final_callback

        self.execute_timeout = execute_timeout

        # check parameters
        assert callable(self._execute_callback), F'executor_callback: {self._execute_callback} must be callable.'
        assert callable(self._initial_callback), f'_initial_callback: {self._initial_callback} must be callable.'

        # initial callback with no parameter
        assert signature(self._initial_callback).parameters == {}, \
            '_initial_callback must have no parameter.'

        # execute callback must have variable parameter
        execute_parameter = signature(self._execute_callback).parameters
        assert Parameter.VAR_KEYWORD in [_.kind for _ in execute_parameter.values()], \
            'executor_callback must have variable parameter.'

        # properties in main process
        self.parameter_queue = queue.Queue()
        self.future_queue = queue.Queue()
        self.submit_lock = threading.Lock()

        # start support threads
        self._send_parameter_thread = Thread(
            target=send_parameter,
            args=(
                self.parameter_queue,
                self._parameter_shared_value,
                self._parameter_ready_event,
                self._parameter_received_event,
            ),
            daemon=True,
        )
        self._send_parameter_thread.start()
        self._send_result_thread = Thread(
            target=send_result,
            args=(
                self.future_queue,
                self._result_shared_value,
                self._result_ready_event,
                self._result_received_event,
            ),
            daemon=True,
        )
        self._send_result_thread.start()

        # start sync
        self._barrier = Barrier(2)

        Process.__init__(self, daemon=True, name=name)
        self.start()

        try:
            self._barrier.wait(initial_timeout)
        except:
            self.exit()
            raise TimeoutError('Executor initial timeout.')

    def run(self) -> None:

        self._initial_callback()
        self._barrier.wait()

        execute_thread: Thread = None
        execute_thread_parameter_queue = queue.Queue()
        execute_thread_result_queue = queue.Queue()

        while True:
            self._parameter_ready_event.wait()
            self._parameter_ready_event.clear()

            start_time = time.time()
            parameter = self._parameter_shared_value.get_object()

            self._parameter_received_event.set()

            # restart execute thread
            if not execute_thread or not execute_thread.is_alive():
                execute_thread_parameter_queue = queue.Queue()
                execute_thread_result_queue = queue.Queue()

                execute_thread = Thread(
                    target=execute_thread_callback,
                    args=(
                        self._execute_callback,
                        execute_thread_parameter_queue,
                        execute_thread_result_queue,
                    ),
                    daemon=True,
                )
                execute_thread.start()

            execute_thread_parameter_queue.put(parameter)

            try:
                result = execute_thread_result_queue.get(timeout=self.execute_timeout)
                if isinstance(result, Exception):
                    executor_result = ExecutorResult(exception=result, start_time=start_time, end_time=time.time())
                else:
                    executor_result = ExecutorResult(result=result, start_time=start_time, end_time=time.time())
            except queue.Empty:
                exception = TimeoutError(f'Executor execute timeout: {self.execute_timeout}')

                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(execute_thread.ident),
                    ctypes.py_object(SystemExit),
                )
                executor_result = ExecutorResult(exception=exception, start_time=start_time, end_time=time.time())

            self._result_shared_value.set_object(executor_result)

            self._result_ready_event.set()

            self._result_received_event.wait()
            self._result_received_event.clear()

    def submit(self, parameter: dict):
        with self.submit_lock:
            future = ExecutorFuture()
            # TODO: extra properties
            future._name = str(self.name)
            self.parameter_queue.put(parameter)
            self.future_queue.put(future)
            return future

    def exit(self):
        self.kill()

        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self._send_parameter_thread.ident),
            ctypes.py_object(SystemExit),
        )
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self._send_result_thread.ident),
            ctypes.py_object(SystemExit),
        )


class ExecutorManager(object):
    executor_mapper: Dict[str, List[Executor]]

    def __init__(self,
                 execute_timeout: int = 5,
                 initial_timeout: int = 5,
                 ):
        self.execute_timeout = execute_timeout
        self.initial_timeout = initial_timeout

        self.executor_mapper = {}

    def register_action(self, action: Union[str, Action], number: int = 1):
        """register an action into manager with number of executors"""
        # find by name
        if isinstance(action, str):
            action = get_registered_actions().get(action)

        # assert
        assert isinstance(action, Action), 'Need an Action instance.'

        # register
        self.executor_mapper[action.name] = [Executor(
            execute_callback=action.action_function,
            initial_callback=action.action_initial_function,
            final_callback=action.action_final_function,

            execute_timeout=self.execute_timeout,
            initial_timeout=self.initial_timeout,

            name=f'{action.name}_{_}',
        ) for _ in range(number)]

    def clear(self):
        while self.executor_mapper:
            _, executors = self.executor_mapper.popitem()
            for executor in executors:
                executor.exit()
