#!/usr/bin/env python

"""\
Check that the input file is a well-formed .screen file.  With '-e',
also check that individual files from patterns in Field_* entries
exist on disk.

If everything is OK, there is no output and the return value is zero.
Otherwise, the return value is nonzero and you should see something on
stderr.
"""

import sys
import os
from argparse import ArgumentParser

from pyidr.file_pattern import FilePattern
from pyidr.screenio import ScreenReader


def parse_cl(argv):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("screen", metavar="SCREEN_FILE", help="screen file")
    parser.add_argument("-e", "--check-existence", action="store_true",
                        help="check existence of individual files in fields")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="verbose mode")
    return parser.parse_args(argv[1:])


# Move to ScreenReader?
def iterfiles(reader):
    for i, w in enumerate(reader.wells):
        for j, pattern in enumerate(w["Fields"]):
            for fn in FilePattern(pattern).filenames():
                yield i, j, fn


def main(argv):
    retval = 0
    args = parse_cl(argv)
    if args.verbose:
        print "checking %r" % (args.screen,)
    with open(args.screen) as f:
        reader = ScreenReader(f)
    # ScreenReader raises an exception if the file is not well-formed
    missing = 0
    for count, (i, j, fn) in enumerate(iterfiles(reader)):
        if args.check_existence and not os.path.exists(fn):
            missing += 1
            retval = 1
            if args.verbose:
                sys.stderr.write("ERROR[%d|%d]: missing %r\n" % (i, j, fn))
    print "files: %d%s" % (
        count + 1, " (missing: %d)" % missing if args.check_existence else ""
    )
    return retval


if __name__ == "__main__":
    sys.exit(main(sys.argv))
