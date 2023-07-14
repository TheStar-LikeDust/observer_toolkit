# coding: utf-8
import pkgutil
from importlib import import_module, reload
from types import ModuleType
from typing import Iterable, Tuple, Type, List

from observer_toolkit.step import Action, get_action, get_registered_actions, DEFAULT_STEP_FIXED_WORKER_FUNCTION, \
    DEFAULT_STEP_TASK_EXPEND_FUNCTION, DEFAULT_EXECUTE_FUNCTION, DEFAULT_ACTION_INITIAL_FUNCTION, \
    DEFAULT_ACTION_FINAL_FUNCTION
from observer_toolkit.observer import Observer


def _get_sub_module_packages(package_path: str) -> Iterable[Tuple[str, str]]:
    """Load a package and return modules

    Node::
        include __init__.py

    """

    target_package = import_module(package_path)

    return [
        (sub_module_info.name, package_path)
        for sub_module_info in pkgutil.iter_modules(target_package.__path__)
    ]


def _find_class_in_module(target_module: ModuleType, target_class: type) -> Iterable[type]:
    """Find class in module"""
    reload(target_module)

    for attr_name in dir(target_module):
        if not attr_name.startswith('_'):
            attr = getattr(target_module, attr_name)

            if isinstance(attr, type) and issubclass(attr, target_class) and attr is not target_class:
                yield attr


def detect_action(
        package_path: str,
        clear_global_actions: bool = True,
        refresh=True,
) -> Iterable[Action]:
    """Detect action in package"""
    if clear_global_actions:
        get_registered_actions().clear()

    actions = []
    for sub_module_name, sub_module_package_path in _get_sub_module_packages(package_path):
        # sub_module = import_module(f'{sub_module_package_path}.{sub_module_name}')
        # import and reload
        sub_module = import_module(f'.{sub_module_name}', package=sub_module_package_path)

        if refresh:
            reload(sub_module)

        # get attr in a module
        action_name = getattr(sub_module, 'action_name', sub_module_name)
        action_initial_function = getattr(sub_module, 'action_initial_function', DEFAULT_ACTION_INITIAL_FUNCTION)
        action_final_function = getattr(sub_module, 'action_final_function', DEFAULT_ACTION_FINAL_FUNCTION)
        action_function = getattr(sub_module, 'action_function', DEFAULT_EXECUTE_FUNCTION)
        step_merged_flag = getattr(sub_module, 'step_merged_flag', False)
        step_task_expend_function = getattr(sub_module, 'step_task_expend_function', DEFAULT_STEP_TASK_EXPEND_FUNCTION)
        step_fixed_worker_function = getattr(sub_module, 'step_fixed_worker_function',
                                             DEFAULT_STEP_FIXED_WORKER_FUNCTION)

        action = get_action(action_name)
        action.action_function = action_function
        action.action_initial_function = action_initial_function
        action.action_final_function = action_final_function
        action.step_merged_flag = step_merged_flag
        action.step_task_expend_function = step_task_expend_function
        action.step_fixed_worker_function = step_fixed_worker_function

        actions.append(action)

    return actions


def detect_observer(
        package_path: str,
        refresh=True,
) -> List[Type[Observer]]:
    """Detect observer in package"""

    observer_classes = []

    for sub_module_name, sub_module_package_path in _get_sub_module_packages(package_path):
        # sub_module = import_module(f'{sub_module_package_path}.{sub_module_name}')
        sub_module = import_module(f'.{sub_module_name}', package=sub_module_package_path)

        if refresh:
            reload(sub_module)

        observer_classes.extend(_find_class_in_module(sub_module, Observer))
    return observer_classes
