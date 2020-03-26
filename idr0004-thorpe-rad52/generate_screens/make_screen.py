#!/usr/bin/env python

import sys
import os
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

ROWS = 8
COLUMNS = 12
FIELDS = 1


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    parser.add_argument("--rev-well-tag", action="store_true",
                        help="well tags are reversed (e.g., 2b instead of b2")
    return parser.parse_args(argv[1:])


def first_existing(d, basenames):
    for bn in basenames:
        fn = os.path.join(d, bn)
        if os.path.exists(fn):
            return fn


def write_screen(data_dir, plate, outf, rev_well_tag=False):
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS)
    for idx in range(ROWS * COLUMNS):
        r, c = writer.coordinates(idx)
        well_tag = "%d%s" % (c, r) if rev_well_tag else "%s%d" % (r, c)
        fn = first_existing(data_dir, [well_tag.lower(), well_tag])
        if fn is None:
            sys.stderr.write("missing: %s\n" %
                             os.path.join(data_dir, well_tag.lower()))
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
    write_screen(args.dir, args.plate, outf, rev_well_tag=args.rev_well_tag)
    if outf is not sys.stdout:
        outf.close()


if __name__ == "__main__":
    main(sys.argv)
