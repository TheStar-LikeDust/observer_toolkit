# coding: utf-8


def func(**kwargs):
    result = kwargs.get('result', 0)
    return result + 100


# def func(**kwargs):
#     result = kwargs.get('iter', list(range(10)))
#
#     return [_ + 100 for _ in result]


action_function = func

action_name = 'sub'

step_task_expend_function = lambda **kwargs: kwargs.get('iter', list(range(5)))

step_merged_flag = True
