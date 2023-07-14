# coding : utf-8

import json
import os
import pickle
import _pickle as cPickle

import time
import random
import numpy
import uuid

from multiprocessing import Pipe, Event, Value, Array
from multiprocessing import Manager, Process

from observer_toolkit.utils._executor import SharedValue


class EchoPipe(Process):
    def __init__(self,
                 receiver,
                 ):
        self.receiver = receiver
        Process.__init__(self, daemon=True)

        self.start()

    def run(self):
        receive_times = []

        for i in range(100):
            obj = self.receiver.recv()
            receive_times.append(time.time())

        print('pipe', receive_times[0], receive_times[-1], 'diff', receive_times[-1] - receive_times[0])


class EchoSV(Process):
    def __init__(self):
        self.shared_value = SharedValue()
        self.parameter_ready_event = Event()
        self.parameter_received_event = Event()

        Process.__init__(self, daemon=True)

        self.start()

    def run(self):
        receive_times = []

        for i in range(100):
            self.parameter_ready_event.wait()
            self.parameter_ready_event.clear()
            obj = self.shared_value.get_object()
            receive_times.append(time.time())
            self.parameter_received_event.set()

        print('sv', receive_times[0], receive_times[-1], 'diff', receive_times[-1] - receive_times[0])


if __name__ == '__main__':
    random_images = [
        numpy.random.randint(0, 255, size=(1080, 1920, 3), dtype=numpy.uint8)
        for _ in range(100)
    ]

    random_images = [
        {
            'image': _,
            'random_bytes': os.urandom(random.randint(1 * 1024 * 1024, 3 * 1024 * 1024)),
            'random_int': random.randint(1 * 1024 * 1024, 3 * 1024 * 1024)
        } for _ in random_images
    ]

    v = Value('i', 0)
    v.value = 10

    print(v.value, int(v.value))

    # exit(0)

    # content_list = [
    #     {
    #         'name': str(uuid.uuid4()),
    #         'age': random.randint(0, 1000),
    #         'other': [uuid.uuid4().hex for _ in range(random.randint(50, 100))],
    #     }
    #
    #     for _ in range(1000)
    # ]
    #
    # s = time.time()
    #
    # pickled = pickle.dumps(content_list, protocol=pickle.HIGHEST_PROTOCOL)
    #
    # print('cost: ', time.time() - s)
    #
    # print('restored: ', pickle.loads(pickled)[0])
    #
    # s = time.time()
    #
    # pickled = cPickle.dumps(content_list)
    #
    # print('cost: ', time.time() - s)
    #
    # print('restored: ', cPickle.loads(pickled)[0])
    #
    # # bytes
    #
    # bytes_content = random.randbytes(10)
    #
    # pickled_bytes = pickle.dumps(bytes_content)
    #
    # print(bytes_content, pickled_bytes)

    # _ForkingPickler

    # receiver, sender = Pipe(False)
    #
    # d = set([1, 2, 3])
    # sender.send(d)
    #
    # d_0 = receiver.recv()
    #
    # print(d, d_0)

    # test
    # pass through pipe
    receiver, sender = Pipe(False)
    last_wait_time = time.time()

    echo = EchoPipe(receiver)

    for image_index in range(100):
        sender.send((random_images[image_index]))
        print('main wait', time.time(), time.time() - last_wait_time)
        last_wait_time = time.time()

    # test
    # pass through Value in thread.

    echo = EchoSV()
    last_wait_time = time.time()
    for image_index in range(100):
        echo.shared_value.set_object(random_images[image_index])

        echo.parameter_ready_event.set()

        echo.parameter_received_event.wait()
        echo.parameter_received_event.clear()
        print('main wait', time.time(), time.time() - last_wait_time)
        last_wait_time = time.time()

    echo.join()
