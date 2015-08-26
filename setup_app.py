"""Script to generate the Windows executable for the app.py file"""
from distutils.core import setup
import py2exe

setup(
    zipfile=None,
    console=['app.py']
)
