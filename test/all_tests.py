import sys
import os
import unittest


def main():
    suite = unittest.defaultTestLoader.discover(os.path.dirname(__file__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return not result.wasSuccessful()


if __name__ == "__main__":
    sys.exit(main())
