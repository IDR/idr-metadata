#!/usr/bin/env python

import glob
import sys
import os
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

ROWS = 6  # A-F
COLUMNS = 8
FIELDS = 6
CHANNEL_NAMES = ("Blue", "Green", "Red", "Yellow")


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
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
    for idx in xrange(ROWS * COLUMNS):
        r, c = writer.coordinates(idx)
        field_values = []

        # These are the different naming structures that are possible.
        for f in range(1, FIELDS+1):
            file_names = None
            for color in CHANNEL_NAMES:
                for alternate in ("A", "B"):
                    for sep in ("-", "_"):
                        for z in ("", "0"):
                            # Input: Plate1-TS-Blue-A
                            # Find: Plate1-Blue-A-TS-0020_A1_01.zvi
                            well_tag = well_tag.replace(
                                "TS-%s-%s" % (color, alternate),
                                "%s-%s-TS" % (color, alternate))
                            pattern = "%s%s%s%s%s%s%s%s.zvi" % (
                                well_tag, "*", sep, r, c, sep, z, f)
                            glob_str = os.path.join(data_dir, pattern)
                            found = glob.glob(glob_str)
                            if not found:
                                continue  # No match
                            elif found == file_names:
                                continue  # Dupe
                            else:
                                assert not file_names
                                file_names = found
            if not file_names:
                field_values.append("")
            else:
                # TODO: do we need a pattern here?
                field_values.append(os.path.join(data_dir, file_names[0]))

        if not any(field_values):
            print >>sys.stderr, "missing well: %s (%s%s)" % (well_tag, r, c)
            field_values = []
        else:
            count += 1
        writer.add_well(field_values)
    if not count:
        raise Exception("no wells: %s" % plate)
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
