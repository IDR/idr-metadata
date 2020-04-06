#!/usr/bin/env python

import sys
import os
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

ROWS = 16
COLUMNS = 24
FIELDS = 1
CHANNEL_NAMES = "FITC", "Hoechst", "Tritc"
TAIL = "_Flo - n000000.tif"
PATTERN = "<%s>%s" % (",".join(CHANNEL_NAMES), TAIL)
EXTRA_KV = {
    "AxisTypes": "C",
    "ChannelNames": ",".join(CHANNEL_NAMES),
}


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    return parser.parse_args(argv[1:])


def has_images(subdir):
    for c in CHANNEL_NAMES:
        fn = os.path.join(subdir, "%s%s" % (c, TAIL))
        if not (os.path.isfile(fn) and os.stat(fn).st_size > 0):
            return False
    return True


def write_screen(data_dir, plate, outf):
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS)
    for idx in range(ROWS * COLUMNS):
        r, c = writer.coordinates(idx)
        well_tag = "Well %s%03d" % (r, c)
        subdir = os.path.join(data_dir, well_tag)
        field_values = []
        if not os.path.isdir(subdir):
            sys.stderr.write("missing: %s\n" % subdir)
        elif not has_images(subdir):
            sys.stderr.write("no images: %s\n" % subdir)
        else:
            field_values.append(os.path.join(subdir, PATTERN))
        writer.add_well(field_values, extra_kv=EXTRA_KV)
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
