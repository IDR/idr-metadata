import os
import unittest


def main():
    suite = unittest.defaultTestLoader.discover(os.path.dirname(__file__))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == "__main__":
    main()
