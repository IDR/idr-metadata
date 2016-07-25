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
#EXTRA_KV = {
#    "AxisTypes": "C",
#    "ChannelNames": ",".join(CHANNEL_NAMES),
#}
#PATTERN_BLOCK = "<%s>" % EXTRA_KV["ChannelNames"]


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    return parser.parse_args(argv[1:])


def write_screen(data_dir, plate, outf):
    # Plate1-TS-Blue-A
    # Plate1-Blue-A-TS-0020_A1_01.zvi
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS)
    for idx in xrange(ROWS * COLUMNS):
        r, c = writer.coordinates(idx)
        well_tag = os.path.basename(data_dir)
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
                            pattern = "%s-%s%s%s%s%s%s%s.zvi" % (
                                well_tag, "*", sep, r, c, sep, z, f)
                            found = glob.glob(os.path.join(data_dir, pattern))
                            if not found:
                                continue  # No match
                            elif found == file_names:
                                continue  # Dupe
                            else:
                                assert not file_names
                                file_names = found
            if not file_names:
                field_values.append(None)
            else:
                # TODO: do we need a pattern here?
                field_values.append(os.path.join(data_dir, file_names[0]))

        writer.add_well(field_values)  # TODO: , extra_kv=EXTRA_KV)
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
