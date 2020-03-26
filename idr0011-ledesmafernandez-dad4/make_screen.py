#!/usr/bin/env python

import glob
import sys
import os
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

ROWS = 6  # A-F
COLUMNS = 8
FIELDS = -1


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    parser.add_argument("-f", "--fields", metavar="FIELDS", help="field count",
                        default=1, type=int)
    return parser.parse_args(argv[1:])


def write_screen(data_dir, plate, outf):

    # For the second screen, remove "-(\d\d)", "-repeated", etc.
    well_tag = os.path.basename(data_dir)
    p1 = well_tag.find("(")
    p2 = well_tag.find(")")
    if p1 > 0 and p2 > 0:
        well_tag = well_tag[0:p1-1]
        well_tag += well_tag[p2:]
    well_tag = well_tag.replace("-repeated", "")
    well_tag = well_tag.replace("-used pics", "")
    # Special case these!
    well_tag = well_tag.replace("Plate1-Blue-A", "P1-Bl-A")
    well_tag = well_tag.replace("Plate2-Red-B", "P2-Red-B")
    well_tag = well_tag.replace("Plate2-Blue-A", "Plate2-Red-B")

    count = 0
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS)
    for idx in range(ROWS * COLUMNS):
        r, c = writer.coordinates(idx)
        field_values = []
        pattern = "*[_-]%s%s[_-]*.[cz][zv]i" % (r, c)
        glob_str = os.path.join(data_dir, pattern)
        found = sorted(glob.glob(glob_str))
        assert str(found), len(found) >= 1 and len(found) <= FIELDS
        for idx in range(FIELDS):
            if found:
                field_values.append(os.path.join(data_dir, found.pop(0)))
            else:
                field_values.append("")

        if not any(field_values):
            print("missing well: %s (%s%s)" % (well_tag, r, c),
                  file=sys.stderr)
            field_values = []
        else:
            count += 1
        writer.add_well(field_values)

    if not count:
        raise Exception("no wells: %s" % plate)
    writer.write(outf)


def main(argv):
    args = parse_cl(argv)
    global FIELDS
    FIELDS = args.fields
    if args.output:
        outf = open(args.output, "w")
    else:
        outf = sys.stdout
    write_screen(args.dir, args.plate, outf)
    if outf is not sys.stdout:
        outf.close()


if __name__ == "__main__":
    main(sys.argv)
