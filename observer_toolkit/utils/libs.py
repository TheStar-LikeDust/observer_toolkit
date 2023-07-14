# coding: utf-8
import ctypes
import gc
import time
from logging import getLogger, Logger
from queue import Queue
from threading import Thread
from typing import Dict, Union, Callable, List, Type, Tuple, Any

from observer_toolkit import get_registered_actions, Step, StepPlan, Observer, get_action
from observer_toolkit.step import Action
from observer_toolkit.utils import GLOBAL_EXECUTOR_MANAGER, ExecutorManager
from observer_toolkit.utils import detect_action, detect_observer
from observer_toolkit.utils._executor import ExecutorFuture
from observer_toolkit.utils._observer_action import execute_observer, initial_observer_wrapper

"""default stdout logger"""
DEFAULT_LOGGER = getLogger(__name__)


def smart_launch(
        action_package: str = 'actions',
        observer_package: str = 'observers',
        action_number_mapper: Dict[str, int] = None,
) -> Tuple[List[Action], List['Type[Observer]']]:
    """smart launch """

    # 0: initial arguments
    action_number_mapper = action_number_mapper or {}

    # 1: detect action
    actions = list(detect_action(package_path=action_package))

    # 2.1: get registered actions
    registered_actions = get_registered_actions().values()

    # 2.2: register global manager
    GLOBAL_EXECUTOR_MANAGER.clear()
    for action in registered_actions:
        GLOBAL_EXECUTOR_MANAGER.register_action(action=action, number=action_number_mapper.get(action.name, 1))

    # 3: detect observer
    observers = list(detect_observer(package_path=observer_package))

    # 4. register observer action
    [register_observer_action(observer_class=observer_class) for observer_class in observers]

    return actions, observers


def smart_run(
        plan: StepPlan,
        executor_manager: ExecutorManager = GLOBAL_EXECUTOR_MANAGER,
        parameter: Dict = None,
        timeout: Union[int, float] = 5,
) -> Dict[str, Any]:
    """smart run"""

    parameter = parameter or {}

    result_mapper = {}

    for level_steps in plan.walk():

        current_parameter = {**parameter, **result_mapper}

        step_future_mapper: Dict[Step, List[ExecutorFuture]] = {}

        for step in level_steps:
            worker_id = step.action.step_fixed_worker_function(**current_parameter)
            expends = step.action.step_task_expend_function(**current_parameter)

            step_future_mapper[step] = [
                executor_manager.executor_mapper[step.name][worker_id].submit({
                    **current_parameter,
                    'result_mapper': result_mapper,
                    'expend': expend,
                })

                for expend in expends
            ]

        for step, step_futures in step_future_mapper.items():
            step_results = [step_future.get_result(timeout=timeout) for step_future in step_futures]

            # expend
            if not step.action.step_merged_flag:
                result_mapper[step.name] = step_results[0]
            else:
                result_mapper[step.name] = step_results

    return result_mapper


def dispatch_parameter(
        dispatch_queue: Queue,
        dispatch_callback: Callable,
        base_cycle: Union[int, float] = 1.0,
        logger: Logger = DEFAULT_LOGGER,
):
    while True:
        try:
            dispatched_parameter = dispatch_callback()
            dispatch_queue.put(dispatched_parameter)
            if not dispatched_parameter:
                break
        except StopIteration:
            logger.info('Dispatch parameter thread exit.')
            break
        except Exception as e:
            logger.error('Dispatch parameter error.', exc_info=e)
            time.sleep(base_cycle * 10)
        finally:
            time.sleep(base_cycle)
    logger.info('Dispatch parameter thread exit.')


def dispatcher_execute(
        dispatch_queue: Queue,
        executor_manager: ExecutorManager,
        finish_callback: Callable[[Dict], None] = None,
        timeout: Union[int, float] = 3.0,
        logger: Logger = DEFAULT_LOGGER,
):
    while True:
        parameter: dict = dispatch_queue.get()

        if parameter:
            if plan := parameter.pop('plan', StepPlan()):
                try:
                    result_mapper = smart_run(
                        plan=plan,
                        executor_manager=executor_manager,
                        timeout=timeout,
                        parameter=parameter,
                    )
                    if finish_callback:
                        finish_callback(result_mapper)
                except Exception as e:
                    logger.error('execute plan failed.', exc_info=e)
            dispatch_queue.task_done()
        else:
            dispatch_queue.task_done()
            break

    logger.info(f'Dispatch execute thread exit.')


def register_observer_action(
        observer_class: Type[Observer],
        executor_manger: ExecutorManager = GLOBAL_EXECUTOR_MANAGER,
        do_duplicate=False):
    observer_action = get_action(observer_class.name)

    observer_action.action_function = execute_observer
    observer_action.action_initial_function = initial_observer_wrapper(observer_class)

    executor_manger.register_action(action=observer_action, number=1)


class DispatcherThreadList(List[Thread]):

    def __init__(self, dispatch_queue: Queue, threads: List[Thread], *args, **kwargs):
        self.dispatch_queue = dispatch_queue
        super().__init__(threads)

    def dispatch_thread_join(self, timeout=None):
        if self:
            self[0].join(timeout=timeout)

    def dispatch_queue_join(self):
        if self.dispatch_queue:
            self.dispatch_queue.join()

    def join(self, timeout=None):
        self.dispatch_thread_join(timeout)
        self.dispatch_queue_join()

    def exit(self):
        for thread in self:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(thread.ident),
                ctypes.py_object(SystemExit)
            )
        gc.collect()


def create_dispatcher(
        dispatch_callback: Callable,
        executor_manager: ExecutorManager = GLOBAL_EXECUTOR_MANAGER,
        finish_callback: Callable[[Dict], None] = None,
        timeout: Union[int, float] = 3.0,
        base_cycle=1,
        worker=10,
        maxsize=128,
        logger: Logger = DEFAULT_LOGGER,
) -> DispatcherThreadList:
    dispatch_queue = Queue(maxsize=maxsize)

    dispatch_parameter_thread = Thread(
        target=dispatch_parameter,
        args=(dispatch_queue, dispatch_callback, base_cycle, logger),
        daemon=True
    )

    dispatch_execute_threads = [
        Thread(
            target=dispatcher_execute,
            args=(dispatch_queue, executor_manager, finish_callback, timeout, logger),
            daemon=True
        )
        for _ in range(worker)
    ]

    threads = [dispatch_parameter_thread, *dispatch_execute_threads]

    [thread.start() for thread in threads]
    return DispatcherThreadList(dispatch_queue=dispatch_queue, threads=threads)
