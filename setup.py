# -*- coding: utf-8 -*-
"""setup with setuptools."""

from setuptools import setup, find_packages
from observer_toolkit import __version__

setup(
    name='observer_toolkit',
    version=__version__,
    description='',
    author='Logic',
    author_email='logic.irl@outlook.com',
    url='https://github.com/TheStar-LikeDust/observer_toolkit',
    python_requires='>=3.8',
    packages=find_packages(exclude=['tests*']),
    license='Apache License 2.0'
)
