#!/usr/bin/env python

import sys
import os
from ConfigParser import ConfigParser
from argparse import ArgumentParser

from pyidr.file_pattern import FilePattern


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("screen", metavar="SCREEN_FILE", help="screen file")
    return parser.parse_args(argv[1:])


def main(argv):
    args = parse_cl(argv)
    cp = ConfigParser()
    cp.optionxform = str
    with open(args.screen) as f:
        cp.readfp(f)
    for sec in cp.sections():
        if not (sec.startswith("Well")):
            continue
        for k in cp.options(sec):
            if not k.startswith("Field_"):
                continue
            pattern = cp.get(sec, k)
            for fn in FilePattern(pattern).filenames():
                if os.path.exists(fn):
                    continue
                sys.stderr.write("ERROR[%s|%s]: missing %r)\n" % (sec, k, fn))


if __name__ == "__main__":
    main(sys.argv)
