#!/usr/bin/env python

import sys
import os
import string
from argparse import ArgumentParser

ROWS = 16
COLUMNS = 24
WELL_LETTERS = string.uppercase[:ROWS]

PLATE = """\
[Plate]
Name = Mitocheck
Rows = %s
Columns = %s
Fields = 1
""" % (ROWS, COLUMNS)

WELL = """\
[Well %(well)s]
Row = %(row)s
Column = %(col)s
"""


def global_idx(i, j):
    return i * COLUMNS + j


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    return parser.parse_args(argv[1:])


def make_well_map():
    wm = {}
    for i, c in enumerate(WELL_LETTERS):
        for j in xrange(COLUMNS):
            wm[global_idx(i, j) + 1] = "%s%d" % (c, j + 1)
    return wm


def write_screen(data_dir, outf):
    outf.write(PLATE)
    for i in xrange(ROWS):
        for j in xrange(COLUMNS):
            outf.write("\n")
            gi = global_idx(i, j)
            outf.write(WELL % {"well": gi, "row": i, "col": j})
            fn = os.path.join(data_dir, "%05d_01.ch5" % (gi + 1))
            if os.path.exists(fn):
                outf.write("Field_0 = %s\n" % fn)
            else:
                sys.stderr.write("missing: %s\n" % fn)


def main(argv):
    args = parse_cl(argv)
    if args.output:
        outf = open(args.output, "w")
    else:
        outf = sys.stdout
    write_screen(args.dir, outf)
    if outf is not sys.stdout:
        outf.close()

    ### do we need this?
    # well_map = make_well_map()
    # with open("map_check.txt", "w") as fo:
    #     for i in sorted(well_map):
    #         fo.write("%d\t%s\n" % (i, well_map[i]))


if __name__ == "__main__":
    main(sys.argv)
