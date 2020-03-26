#!/usr/bin/env python

import sys
import os
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

ROWS = 16
COLUMNS = 24
FIELDS = 2
CHANNEL_NAMES = "A", "H", "T"
EXTRA_KV = {
    "AxisTypes": "C",
    "ChannelNames": ",".join(CHANNEL_NAMES),
}
PATTERN_BLOCK = "<%s>" % EXTRA_KV["ChannelNames"]


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    return parser.parse_args(argv[1:])


def get_patterns(subdir):
    w = os.path.basename(subdir.rstrip(os.sep))
    basenames = set(_ for _ in os.listdir(subdir) if _.endswith(".tif"))
    expected_names = set("%s_%s%d.tif" % (w, c, f)
                         for c in CHANNEL_NAMES
                         for f in range(1, FIELDS + 1))
    expected_patterns = ["%s_%s%d.tif" % (w, PATTERN_BLOCK, _)
                         for _ in range(1, FIELDS + 1)]
    if basenames == expected_names:
        return expected_patterns
    # a small number of wells have leading tildes in the file names
    elif basenames == set("~" + _ for _ in expected_names):
        return ["~" + _ for _ in expected_patterns]
    else:
        return []


def write_screen(data_dir, plate, outf):
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS)
    for idx in range(ROWS * COLUMNS):
        r, c = writer.coordinates(idx)
        well_tag = "%s%s%03d" % (os.path.basename(data_dir), r, c)
        subdir = os.path.join(data_dir, well_tag)
        field_values = []
        if not os.path.isdir(subdir):
            sys.stderr.write("missing: %s\n" % subdir)
        else:
            patterns = get_patterns(subdir)
            if not patterns:
                sys.stderr.write("missing images: %s\n" % subdir)
            for p in patterns:
                field_values.append(os.path.join(subdir, p))
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
