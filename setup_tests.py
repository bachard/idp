"""Script to generate the Windows executable for the tests.py file"""
from distutils.core import setup
import py2exe

setup(
    zipfile=None,
    console=['tests.py']
)
