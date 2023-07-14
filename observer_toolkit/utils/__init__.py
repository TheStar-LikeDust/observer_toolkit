# coding: utf-8


from ._executor import ExecutorManager

GLOBAL_EXECUTOR_MANAGER = ExecutorManager()

# common

from ._detect import detect_action, detect_observer
from .libs import smart_launch, smart_run, create_dispatcher
