"""Script to generate the Windows executable for the client.py file"""
from distutils.core import setup
import py2exe

setup(
    zipfile=None,
    windows=['client.py']
)
