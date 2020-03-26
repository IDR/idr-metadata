#!/usr/bin/env python

import sys
import os
import re
from collections import OrderedDict
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

ROWS = 22
COLUMNS = 18
FIELDS = 1

SUB_PATTERN = re.compile(r"([A-Z])(\d+)")


def find_pattern(d):
    char_map = OrderedDict()
    for fn in os.listdir(d):
        for c, n in re.findall(SUB_PATTERN, fn):
            char_map.setdefault(c, []).append(n)
    if not char_map:
        return None
    pattern = [".ome.tif"]
    while char_map:
        c, values = char_map.popitem()
        fmt = "%%0%dd" % max(map(len, values))
        values = map(int, values)
        start, stop = min(values), max(values)
        if start != stop:
            pattern.append("--%s<%s-%s>" % (c, fmt % start, fmt % stop))
        else:
            pattern.append("--%s%s" % (c, fmt % start))
    pattern.append("image")
    return "".join(reversed(pattern))


def write_screen(data_dir, plate, outf, screen=None):
    kwargs = {"screen_name": screen} if screen else {}
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS, **kwargs)
    for i in range(ROWS):
        for j in range(COLUMNS):
            x, y = j, i
            subdir = os.path.join(data_dir, "field--X%02d--Y%02d" % (x, y))
            field_values = []
            if not os.path.isdir(subdir):
                sys.stderr.write(
                    "WARNING: no subdir for X=%d, Y=%d (%s)\n" %
                    (x, y, subdir)
                )
            else:
                pattern = find_pattern(subdir)
                if pattern is not None:
                    field_values.append(os.path.join(subdir, pattern))
                else:
                    sys.stderr.write(
                        "WARNING: no images in subdir for X=%d, Y=%d (%s)\n" %
                        (x, y, subdir)
                    )
            writer.add_well(field_values)
    writer.write(outf)


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    parser.add_argument("-s", "--screen", metavar="SCREEN", help="screen name")
    return parser.parse_args(argv[1:])


def main(argv):
    args = parse_cl(argv)
    if args.output:
        outf = open(args.output, "w")
    else:
        outf = sys.stdout
    write_screen(args.dir, args.plate, outf, screen=args.screen)
    if outf is not sys.stdout:
        outf.close()


if __name__ == "__main__":
    main(sys.argv)
