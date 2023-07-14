import os
import unittest

from observer_toolkit.utils._executor import SharedValue

import pickle
import random
from multiprocessing import Value, Array


class MyTestCase(unittest.TestCase):

    def test_shared_value(self):
        a = Array('c', 4 * 1024 * 1024)
        obj = {
            'random_bytes': os.urandom(random.randint(1, 1024 * 1024))
        }

        pickled = pickle.dumps(obj)
        pickled_len = len(pickled)


        a.value = pickled

        print(len(a.raw), len(a.value))

        shared_value_bytes = a.raw[:pickled_len]

        new_obj = pickle.loads(shared_value_bytes)

        self.assertEqual(obj, new_obj)

        # pickled = pickle.dumps(obj)
        #
        #
        # sv_bytes = a.value
        #
        # print(len(sv_bytes), len(a.value[:1000]), len(pickled))
        #
        # pickle.loads(sv_bytes)


if __name__ == '__main__':
    unittest.main()
