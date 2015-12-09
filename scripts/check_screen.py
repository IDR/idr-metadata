#!/usr/bin/env python

import sys
import os
from argparse import ArgumentParser

from pyidr.file_pattern import FilePattern
from pyidr.screenio import ScreenReader


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("screen", metavar="SCREEN_FILE", help="screen file")
    return parser.parse_args(argv[1:])


def main(argv):
    args = parse_cl(argv)
    with open(args.screen) as f:
        reader = ScreenReader(f)
    for i, w in enumerate(reader.wells):
        for j, pattern in enumerate(w["Fields"]):
            for fn in FilePattern(pattern).filenames():
                if os.path.exists(fn):
                    continue
                sys.stderr.write("ERROR[%d|%d]: missing %r\n" % (i, j, fn))


if __name__ == "__main__":
    main(sys.argv)
