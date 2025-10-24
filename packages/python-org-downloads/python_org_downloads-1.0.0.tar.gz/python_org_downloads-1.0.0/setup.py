#!python
"""A setuptools based setup module.

ToDo:
- Everything
"""

from setuptools import setup

from simplifiedapp import object_metadata

import python_org_downloads

setup(**object_metadata(python_org_downloads))
