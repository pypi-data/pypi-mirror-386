import unittest

from IPython.lib.pretty import pretty

from ptetools.collections import fnamedtuple


class TestCollections(unittest.TestCase):
    def test_fnamedtuple(self):
        Point = fnamedtuple("Point", ["x", "y"])
        pt = Point(2, 3)
        p = pretty(pt)
        assert "Point" in p


if __name__ == "__main__":
    unittest.main()
