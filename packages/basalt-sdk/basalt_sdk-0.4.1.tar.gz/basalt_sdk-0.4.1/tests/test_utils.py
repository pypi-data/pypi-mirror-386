import unittest
from parameterized import parameterized
from basalt.utils.utils import pick_typed, pick_number

class TestUtils(unittest.TestCase):

	@parameterized.expand([
		({ "a": 1 }, int, True),
		({ "a": 1 }, float, False),
		({ "a": 2. }, float, True),
		({ "a": "1" }, str, True),
		({ "a": 1 }, bool, False),
		({ "a": 0 }, bool, False),
		({ "a": True, }, bool, True),
		({ "a": False }, bool, True),
		({ "a": False }, int, False),
		({ "a": True }, int, False),
	])
	def test_pick_typed(self, d, expected_type, succeeds):
		if succeeds:
			val = pick_typed(d, "a", expected_type)	
			self.assertIsInstance(val, expected_type)		
		else:
			with self.assertRaises(Exception):
				pick_typed(d, "a", expected_type)
    
	@parameterized.expand([
		({ "a": 1 }, int),
		({ "a": 1. }, float),
		({ "a": 2.78998 }, float),
		({ "a": -1 }, int),
		({ "a": -1.9 }, float),
		({ "a": "1" }, None),
		({ "a": True, }, None),
		({ "a": False }, None),
	])
	def test_pick_number(self, d, expected_type):
		if expected_type:
			val = pick_number(d, "a")
			self.assertIsInstance(val, expected_type)
		else:
			with self.assertRaises(Exception):
				pick_number(d, "a")