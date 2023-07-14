# coding: utf-8


def func(**kwargs):
    print('image shape', kwargs.get('image').shape)
    return list(range(5))


action_function = func

action_name = 'iter'
