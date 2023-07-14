# coding: utf-8
from logging import Logger, getLogger
from typing import Any, Dict, List, Deque, Callable, Literal, Tuple, Optional, Type, Union

from observer_toolkit import Step, StepPlan

OBSERVER_EXECUTE_STATUS = Literal[-1, 0, 1]
"""status of observer execute"""

OBSERVER_JUDGE_STATUS_MAPPER = {
    -1: 'Error',
    0: 'Not Ready',
    1: 'Judged',
}
"""status mapper of observer judge"""

OBSERVER_TRIGGER_STATUS_MAPPER = {
    -1: 'Error',
    0: 'Not Ready',
    1: 'Triggered',
}
"""status mapper of observer trigger"""

GLOBAL_OBSERVER_CLASS_MAPPER: Dict[str, Type['Observer']] = {}
"""global observer mapper."""

# TODO:
SUPER_NAMES = ['Observer', 'BaseObserver', 'ObserverMeta', 'JudgeMixin', 'TriggerMixin']
"""Fixed names of observer super class."""


def DEFAULT_JUDGE_CALLBACK(**kwargs) -> bool:
    """Default judge callback"""
    return False


def DEFAULT_TRIGGER_CALLBACK(**kwargs) -> Any:
    """Default trigger callback"""
    return None


def get_observers() -> List[Type['Observer']]:
    return list(GLOBAL_OBSERVER_CLASS_MAPPER.values())


get_observer = get_observers


class ObserverMeta(type):
    """Observer元类"""

    def __new__(mcs, name, bases, attrs):
        # name
        attrs['name'] = name

        # step plan
        plan = StepPlan()
        [plan.append(step) for step in attrs.get('steps', [])]
        attrs['plan'] = plan

        judge_callback = attrs.pop('judge_callback', DEFAULT_JUDGE_CALLBACK)
        trigger_callback = attrs.pop('trigger_callback', DEFAULT_TRIGGER_CALLBACK)
        cls = super().__new__(mcs, name, bases, attrs)
        cls.callback = [judge_callback, trigger_callback]

        if name not in SUPER_NAMES and name not in GLOBAL_OBSERVER_CLASS_MAPPER:
            GLOBAL_OBSERVER_CLASS_MAPPER[name] = cls
        return cls


class BaseObserver(object, metaclass=ObserverMeta):
    name: str = None
    steps: List[Step] = []

    plan: StepPlan = None

    judge_callback: Callable
    trigger_callback: Callable
    callback: Tuple[Callable, Callable] = None

    logger: Logger


class SlidingWindowDeque(Deque[bool]):

    def __init__(self, maxlen: int = 10):
        super().__init__(maxlen=maxlen)
        self.refill()

    def append_true(self):
        """添加True"""
        self.append(True)

    def get_rate(self, round_num: int = 2) -> float:
        """获取队列中True的比例, 默认保留两位小数"""
        return round(len(list(filter(lambda x: x, self))) / self.maxlen, round_num)

    def refill(self, fill_value: Any = False, ) -> None:
        """重新填充"""
        [self.append(fill_value) for _ in range(self.maxlen)]

    def clear(self) -> None:
        self.refill()


class JudgeMixin(BaseObserver):
    receive_action_names: List[str]
    """接收的节点名称"""

    result_mapper_buffer: Dict[str, Any] = None
    """结果缓存"""

    judge_result_mapper: Dict[str, Any] = None
    _judge_result_deque: SlidingWindowDeque = None
    """判断结果和识别结果缓存队列 - 滑动窗口"""

    def __init__(self,
                 receive_node_names: List[str],
                 judge_callback: Callable = None,
                 ):
        self.receive_action_names = receive_node_names
        self.judge_callback = judge_callback

        # init
        self.result_mapper_buffer: Dict[str, Any] = {}

    def _update_result_buffer(self, result_mapper: Dict[str, Any]) -> None:
        """更新结果"""

        [
            self.result_mapper_buffer.__setitem__(node_name, result_mapper[node_name])
            for node_name in self.receive_action_names
            if node_name in result_mapper and node_name not in self.result_mapper_buffer
        ]

    def _ready_to_judge(self) -> bool:
        """检查是否执行"""
        return all([node_name in self.result_mapper_buffer for node_name in self.receive_action_names])

    def judge(self,
              parameter: dict
              ) -> Tuple[
        OBSERVER_EXECUTE_STATUS, Optional[Any]]:
        """接收结果并判断"""

        self._update_result_buffer(parameter)
        if self._ready_to_judge():
            self.judge_result_mapper = self.result_mapper_buffer.copy()
            try:
                result = self.judge_callback(**{
                    **parameter,
                    # buffer after parameter to avoid override
                    **self.result_mapper_buffer,
                    'ob': self
                })
                self._judge_result_deque.append(bool(result))
            except Exception as e:
                self.logger.error(f'Observer Judge Error: {e}')
                return -1, e
            else:
                return 1, result
            finally:
                self.result_mapper_buffer.clear()
        return 0, None


class TriggerMixin(BaseObserver):
    """触发"""

    trigger_cache_length: int = 10
    """滑动窗口长度 == 队列长度"""

    trigger_rate: float = 0.5
    """滑动窗口中的达到触发预警的比例"""

    _judge_result_deque: SlidingWindowDeque = None
    """判断结果和识别结果缓存队列 - 滑动窗口"""

    judge_result_mapper: Dict[str, Any] = None

    def __init__(self, trigger_callback: Callable):
        """初始化"""

        # initial
        self.trigger_callback = trigger_callback

    def trigger(self, parameter: dict) -> Tuple[OBSERVER_EXECUTE_STATUS, Optional[Any]]:
        """检查是否触发报警"""

        if self._judge_result_deque.get_rate() >= self.trigger_rate:

            # clear judge result
            self._judge_result_deque.clear()
            try:
                result = self.trigger_callback(**{**parameter, **self.judge_result_mapper, 'ob': self})
            except Exception as e:
                return -1, e
            else:
                return 1, result
        return 0, None


class Observer(JudgeMixin, TriggerMixin):
    ready_status: bool = True
    """是否准备就绪"""

    def __init__(self,
                 logger=getLogger(__name__),
                 ):
        self.logger = logger

        plan = StepPlan()
        [plan.append(step) for step in self.steps]

        # common init
        self._judge_result_deque = SlidingWindowDeque(maxlen=self.trigger_cache_length)

        JudgeMixin.__init__(self, [step.name for step in self.steps], self.callback[0])
        TriggerMixin.__init__(self, self.callback[1])

    def ready(self) -> bool:
        return self.ready_status

    def do_action(self, parameter: Dict) -> Optional[Tuple[Tuple[int, Any], Tuple[int, Any]]]:
        if self.ready():
            judge_status = self.judge(parameter)
            trigger_status = self.trigger(parameter)
            return judge_status, trigger_status


def merge_plan(observers: List[Union[Observer, Type[Observer], ObserverMeta]], observer_action: bool = True):
    plan = StepPlan()

    # ready observers' plan
    ready_observers = [observer for observer in observers if observer.ready()]
    [plan.extend(observer.steps) for observer in ready_observers]

    # add observer action
    if observer_action:
        current_dependencies = plan.current_dependencies()
        [plan.append(Step(action=observer.name, dependency_actions=current_dependencies))
         for observer in observers if observer.ready()]
    return plan
