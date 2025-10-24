#!python
"""
"""

from simplifiedapp import main

try:
	import python_org_downloads
except ModuleNotFoundError:
	import __init__ as python_org_downloads

main(python_org_downloads)
