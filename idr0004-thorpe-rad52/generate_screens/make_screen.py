#!/usr/bin/env python

import sys
import os
from argparse import ArgumentParser

from screenio import ScreenWriter

ROWS = 8
COLUMNS = 12
FIELDS = 1


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    return parser.parse_args(argv[1:])


def write_screen(data_dir, plate, outf):
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS)
    for idx in xrange(ROWS * COLUMNS):
        r, c = writer.coordinates(idx)
        well_tag = "%s%d" % (r.lower(), c)
        fn = os.path.join(data_dir, well_tag)
        if not os.path.isfile(fn):
            sys.stderr.write("missing: %s\n" % fn)
            field_values = None
        else:
            field_values = [fn]
        writer.add_well(field_values)
    writer.write(outf)


def main(argv):
    args = parse_cl(argv)
    if args.output:
        outf = open(args.output, "w")
    else:
        outf = sys.stdout
    write_screen(args.dir, args.plate, outf)
    if outf is not sys.stdout:
        outf.close()


if __name__ == "__main__":
    main(sys.argv)
