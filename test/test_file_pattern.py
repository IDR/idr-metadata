import unittest

import pyidr.file_pattern as fp


class TestRange(unittest.TestCase):

    def setUp(self):
        self.bad = [
            ("0-2:a", ValueError),
            ("!-A", ValueError),
            ("a-E", ValueError),
            ("A-e", ValueError),
            ("2-1", ValueError),
            ("B-A", ValueError),
            ("1-k", ValueError),
            ("a-9", ValueError),
        ]
        self.good = [
            ("9", ["9"]),
            ("0-2", ["0", "1", "2"]),
            ("9-11", ["9", "10", "11"]),
            ("09-11", ["09", "10", "11"]),
            ("1-5:2", ["1", "3", "5"]),
            ("Q", ["Q"]),
            ("A-C", ["A", "B", "C"]),
            ("A-E:2", ["A", "C", "E"]),
            ("q", ["q"]),
            ("a-c", ["a", "b", "c"]),
            ("a-e:2", ["a", "c", "e"]),
        ]

    def test_bad(self):
        for r, exc in self.bad:
            self.assertRaises(exc, fp.expand_range, r)

    def test_good(self):
        for r, exp in self.good:
            self.assertEqual(fp.expand_range(r), exp)


class TestBlock(unittest.TestCase):

    def setUp(self):
        self.good = [
            ("1,5-7", ["1", "5", "6", "7"]),
            ("Red,Green,Blue", ["Red", "Green", "Blue"]),
        ]

    def runTest(self):
        for b, exp in self.good:
            self.assertEqual(fp.expand_block(b), exp)


class TestPattern(unittest.TestCase):

    def setUp(self):
        self.blocks = ["0-1", "R,G,B", "10-30:10"]
        self.string_pattern = "z<%s>c<%s>t<%s>.tif" % tuple(self.blocks)
        self.pattern = fp.FilePattern(self.string_pattern)
        self.expected_fnames = [
            "z0cRt10.tif",
            "z0cRt20.tif",
            "z0cRt30.tif",
            "z0cGt10.tif",
            "z0cGt20.tif",
            "z0cGt30.tif",
            "z0cBt10.tif",
            "z0cBt20.tif",
            "z0cBt30.tif",
            "z1cRt10.tif",
            "z1cRt20.tif",
            "z1cRt30.tif",
            "z1cGt10.tif",
            "z1cGt20.tif",
            "z1cGt30.tif",
            "z1cBt10.tif",
            "z1cBt20.tif",
            "z1cBt30.tif",
        ]

    def test_blocks(self):
        self.assertEqual(self.pattern.blocks(), self.blocks)

    def test_filenames(self):
        self.assertEqual(
            set(self.pattern.filenames()), set(self.expected_fnames)
        )


def load_tests(loader, tests, pattern):
    test_cases = (TestRange, TestBlock, TestPattern)
    suite = unittest.TestSuite()
    for tc in test_cases:
        suite.addTests(loader.loadTestsFromTestCase(tc))
    return suite


if __name__ == "__main__":
    suite = load_tests(unittest.defaultTestLoader, None, None)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
