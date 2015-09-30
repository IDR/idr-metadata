#!/usr/bin/env python

import sys
import os
import string
from argparse import ArgumentParser

ROWS = 16
COLUMNS = 24
FIELDS = 1
WELL_LETTERS = string.uppercase[:ROWS]

PLATE = """\
[Plate]
Name = %%s
Rows = %s
Columns = %s
Fields = %s
""" % (ROWS, COLUMNS, FIELDS)

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
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    return parser.parse_args(argv[1:])


def make_well_map():
    wm = {}
    for i, c in enumerate(WELL_LETTERS):
        for j in xrange(COLUMNS):
            wm[global_idx(i, j)] = "%s%03d" % (c, j + 1)
    return wm


def write_screen(data_dir, plate, outf):
    wm = make_well_map()
    outf.write(PLATE % plate)
    for i in xrange(ROWS):
        for j in xrange(COLUMNS):
            outf.write("\n")
            gi = global_idx(i, j)
            outf.write(WELL % {"well": gi, "row": i, "col": j})
            well_tag = "Well %s" % wm[gi]
            subdir = os.path.join(data_dir, well_tag)
            if not os.path.isdir(subdir):
                sys.stderr.write("missing: %s\n" % subdir)
                continue
            pattern = "<FITC,Hoechst,Tritc>_Flo - n000000.tif"
            fn = os.path.join(subdir, pattern)
            outf.write("Field_0 = %s\n" % fn)


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
