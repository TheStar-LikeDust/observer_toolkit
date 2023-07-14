# coding: utf-8
import time

import cv2

from observer_toolkit import smart_launch, smart_run, get_observer, create_dispatcher, merge_plan
from observer_toolkit.utils import GLOBAL_EXECUTOR_MANAGER
from observer_toolkit.utils.libs import register_observer_action

if __name__ == '__main__':

    # smart initial function:
    # 1. detect action
    # 2. initial executors

    smart_launch(
        action_package=r'tests.unittests.mock_packages.mock_actions',
        observer_package=r'tests.unittests.mock_packages.mock_observers',
        action_number_mapper={
        }
    )

    observers = [observer_class() for observer_class in get_observer() if observer_class.name == 'MockObserver']

    count = 50
    v = cv2.VideoCapture(r'/mnt/luoji/observer_components/test_videos.mp4')


    def dispatch_func():

        if v.isOpened():
            for i in range(count):
                yield {
                    'i': i,
                    'image': v.read()[1],
                    'plan': merge_plan(observers)
                }
            yield None


    f = dispatch_func()


    def finish_func(result_mapper):
        print(result_mapper)


    dispatch_thread = create_dispatcher(
        dispatch_callback=lambda: next(f),
        finish_callback=finish_func,
        base_cycle=0.5,
        worker=10,
    )

    dispatch_thread.join()
    print('done')
