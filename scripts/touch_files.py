#!/usr/bin/env python

"""\
Touch every file in a .screen.

Can be used to set up a directory tree for testing.
"""

import sys
import os
import errno
from argparse import ArgumentParser

from pyidr.file_pattern import FilePattern
from pyidr.screenio import ScreenReader


def parse_cl(argv):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("screen", metavar="SCREEN_FILE", help="screen file")
    return parser.parse_args(argv[1:])


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


# Move to ScreenReader?
def iterfiles(reader):
    for i, w in enumerate(reader.wells):
        for j, pattern in enumerate(w["Fields"]):
            for fn in FilePattern(pattern).filenames():
                yield i, j, fn


def main(argv):
    args = parse_cl(argv)
    with open(args.screen) as f:
        reader = ScreenReader(f)
    for i, j, fn in iterfiles(reader):
        try:
            os.makedirs(os.path.dirname(fn))
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass
        touch(fn)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
