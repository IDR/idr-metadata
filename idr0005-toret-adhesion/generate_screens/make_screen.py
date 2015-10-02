#!/usr/bin/env python

import sys
import os
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

ROWS = 8
COLUMNS = 12
FIELDS = 3


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    return parser.parse_args(argv[1:])


def _get_well_map(d):
    m = {}
    for bn in os.listdir(d):
        if not bn.endswith(".tif"):
            continue
        _, well_tag, field_tag, rest = bn.split("_", 3)
        if rest.startswith("thumb"):
            continue
        fn = os.path.join(d, bn)
        m.setdefault(well_tag, {}).setdefault(field_tag, []).append(fn)
    return m


def write_screen(data_dir, plate, outf):
    well_map = _get_well_map(data_dir)
    #--
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS)
    for idx in xrange(ROWS * COLUMNS):
        well_tag = "%s%02d" % writer.coordinates(idx)
        try:
            field_map = well_map[well_tag]
        except KeyError:
            sys.stderr.write("%s: missing well: %s\n" % (data_dir, well_tag))
            continue
        try:
            field_values = [
                field_map["s%d" % _][0] for _ in xrange(1, FIELDS + 1)
            ]
        except (KeyError, IndexError):
            sys.stderr.write("%s: missing fields for well %s\n" % (
                data_dir, well_tag
            ))
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
