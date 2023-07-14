# coding: utf-8

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import chain
from typing import Optional, List, Dict, Any, Sequence, Set, Union, Iterable
from types import FunctionType

GLOBAL_ACTION_REGISTRY: Dict[str, Action] = {}


def DEFAULT_EXECUTE_FUNCTION(*args, **kwargs):
    """Default func func."""
    return {'args': args, **kwargs}


def DEFAULT_STEP_TASK_EXPEND_FUNCTION(**kwargs) -> list:
    """Default step task expend func."""
    return [None]


def DEFAULT_STEP_FIXED_WORKER_FUNCTION(**kwargs) -> Optional[int]:
    """Default step fixed worker func."""
    return 0


def DEFAULT_ACTION_INITIAL_FUNCTION():
    """do nothing"""
    return None


def DEFAULT_ACTION_FINAL_FUNCTION():
    """do nothing"""
    return None


def get_registered_actions() -> Dict[str, Action]:
    """Get all registered actions."""
    return GLOBAL_ACTION_REGISTRY


def clear_registered_actions():
    """Clear all registered actions."""
    GLOBAL_ACTION_REGISTRY.clear()


def get_action(action_name: str) -> Action:
    if action := GLOBAL_ACTION_REGISTRY.get(action_name):
        return action
    return Action(name=action_name)


@dataclass()
class Action(object):
    name: str = field()
    action_function: FunctionType = field(default=DEFAULT_EXECUTE_FUNCTION)
    action_initial_function: FunctionType = field(default=DEFAULT_ACTION_INITIAL_FUNCTION)
    action_final_function: FunctionType = field(default=DEFAULT_ACTION_FINAL_FUNCTION)

    step_merged_flag: bool = field(default=False)
    step_task_expend_function: FunctionType = field(default=DEFAULT_STEP_TASK_EXPEND_FUNCTION)
    step_fixed_worker_function: FunctionType = field(default=DEFAULT_STEP_FIXED_WORKER_FUNCTION)

    def __new__(cls, *args, **kwargs):
        # create instance
        instance = super().__new__(cls)

        # get the name argument
        name = kwargs.get('name', args[0] if len(args) > 0 else None)
        if name is None:
            raise TypeError('name is required')

        # return the singleton instance
        singleton_instance = GLOBAL_ACTION_REGISTRY.setdefault(name, instance)

        return singleton_instance

    def __repr__(self):
        """name and action_function"""
        return f'<Action name: "{self.name}" from: "{self.action_function.__module__}">'

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return hash(
            (
                self.name,
                self.action_function.__code__,
                self.action_initial_function.__code__,
                self.action_final_function.__code__,
                self.step_task_expend_function.__code__,
                self.step_fixed_worker_function.__code__
            )
        )


@dataclass
class Step(object):
    action: Union[Action, str] = field(default=None)
    # TODO: fix the type
    dependency_actions: 'Union[List[Action], Set[Action], Iterable[str]]' = field(default_factory=list)

    def __post_init__(self):
        self.action = get_action(action_name=self.action) if isinstance(self.action, str) else self.action

        # self.dependency_actions = set(self.dependency_actions)
        self.dependency_actions = set([
            get_action(depend) if isinstance(depend, str) else depend
            for depend in self.dependency_actions
        ])

    @property
    def name(self):
        return self.action.name

    def __repr__(self):
        return f'<Step name: "{self.name}" dependency_actions: {[_.name for _ in self.dependency_actions]}>'

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return hash((self.name, tuple(self.dependency_actions)))


class StepPlan(List[Step]):

    @property
    def names(self):
        return [step.name for step in self]

    def append(self, __object: Step) -> None:
        if __object.name not in self.names:
            super().append(__object)
        else:
            self[self.names.index(__object.name)].dependency_actions.update(__object.dependency_actions)

    def extend(self, __iterable: Iterable[Step]) -> None:
        [self.append(step) for step in __iterable]

    def current_dependencies(self) -> List[str]:
        """Get the current dependencies."""
        return [step.name for step in chain(*self.walk())]

    def check_if_isolated(self, step: Step) -> bool:
        """Check if the step is isolated."""
        print('nothing here')
        return False
        # TODO:

    def walk(self) -> Sequence[Sequence[Step]]:
        """Walk the step."""

        step_sequence = []

        while True:
            # get current set of steps and actions
            current_steps = list(chain(*step_sequence))
            current_actions = set([step.action for step in current_steps])

            if next_steps := [
                step for step in self
                if step.dependency_actions.issubset(current_actions) and step not in current_steps
            ]:
                step_sequence.append(next_steps)
            else:
                break

        return step_sequence


def execute_plan(plan: StepPlan, parameters: Dict[str, Any] = None):
    """Execute the plan."""

    result_mapper = {}

    for step_sequence in plan.walk():
        for step in step_sequence:
            result = step.action.action_function(**parameters)
            result_mapper[step.name] = result

    return result_mapper
