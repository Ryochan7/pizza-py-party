#!/usr/bin/env python

from setuptools import setup

import pizza_py_party

setup(
    name='pizza-py-party',
    version=pizza_py_party.__version__,
    author='Travis Nickles',
    py_modules=['pizza_py_party'],
    description="Script for ordering pizza through the Domino's web interface",
    url='http://code.google.com/p/pizza-py-party/',
    classifiers=[
        "Environment :: Console",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
