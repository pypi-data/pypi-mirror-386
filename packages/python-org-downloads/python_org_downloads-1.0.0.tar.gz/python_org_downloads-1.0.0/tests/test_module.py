#!python
"""
Testing the whole module
"""

from unittest import TestCase

import python_org_downloads


class ModuleTest(TestCase):
	"""
	Tests for the module
	"""
	def test_dummy(self):
		"""
		Dummy test, checking for correct syntax
		"""

		python_org_downloads
		self.assertEqual(True, True)  # add assertion here
