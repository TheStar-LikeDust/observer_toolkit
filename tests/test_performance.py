# coding: utf-8
import time

import cv2
import numpy

from observer_toolkit import smart_launch, smart_run, get_observer, create_dispatcher, merge_plan, StepPlan, Step

from threading import Thread

if __name__ == '__main__':

    smart_launch(
        action_package=r'tests.unittests.mock_packages.mock_actions',
        observer_package=r'tests.unittests.mock_packages.mock_observers',
    )

    random_images = [
        numpy.random.randint(0, 255, size=(1080, 1920, 3), dtype=numpy.uint8)
        for _ in range(100)
    ]

    observers = [observer_class() for observer_class in get_observer() if observer_class.name == 'PerformanceObserver']

    plan = merge_plan(observers)


    def dispatch_func():
        for image in random_images:
            yield {
                'plan': plan,
                'image': image,
            }
            print('gen')
        yield False


    count = 0


    def finish_callback(result_mapper):
        global count
        count += 1
        print('finish', count, result_mapper.get('PerformanceObserver'))


    generator = dispatch_func()

    print('create dispatcher')
    dispatch_thread = create_dispatcher(
        dispatch_callback=lambda: next(generator),
        finish_callback=finish_callback,
        base_cycle=0.05,
        worker=10,
    )
    s = time.time()
    dispatch_thread.dispatch_thread_join()
    print(time.time() - s)

    dispatch_thread.exit()
