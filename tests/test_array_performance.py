# -*- coding: utf-8 -*-
"""Performance


"""
import ctypes
import os
import random
import time
from multiprocessing import Array

if __name__ == '__main__':
    length = 64 * 1024 * 1024
    array = Array('c', length)
    number = 32
    last_index = 0

    random_content_list = [os.urandom(random.randint(8 * 1024 * 1024, 12 * 1024 * 1024)) for _ in range(1)]

    # dump
    s = time.time()
    for i in range(number):
        last_index = i % 1
        random_content = random_content_list[last_index]
        array.value = random_content

    cost = time.time() - s

    print('cost', round(time.time() - s, 6), 'average', round(cost / number, 6))

    # load
    s = time.time()
    for i in range(number):
        bytes_content = bytes(array.raw)

    cost = time.time() - s
    print('cost', round(time.time() - s, 6), 'average', round(cost / number, 6))

    # load by ctypes
    s = time.time()
    for i in range(number):
        c_array = ctypes.cast(array.get_obj(), ctypes.POINTER(ctypes.c_char * length))
        bytes_content = ctypes.string_at(c_array, length * ctypes.sizeof(ctypes.c_char))

    cost = time.time() - s
    print('cost', round(time.time() - s, 6), 'average', round(cost / number, 6))

    # load by stackoverflow
    s = time.time()
    for i in range(number):
        memory = memoryview(array.value)

    cost = time.time() - s
    print('cost', round(time.time() - s, 6), 'average', round(cost / number, 6))

    # load by stackoverflow
    s = time.time()
    for i in range(number):
        bytes_content = bytes(memoryview(array.value))

    cost = time.time() - s
    print('cost', round(time.time() - s, 6), 'average', round(cost / number, 6))
