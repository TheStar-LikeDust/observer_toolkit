# coding: utf-8
import cv2


def func(**kwargs):
    image = kwargs.get('expend')

    # cv2 reshape to 50*50
    # image = cv2.resize(image, (50, 50, 3))

    return image.shape


action_function = func

action_name = 'performance_sub'

step_task_expend_function = lambda **kwargs: kwargs.get('performance_iter', list(range(5)))

step_merged_flag = True
