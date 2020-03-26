#!/usr/bin/env python

import sys
import os
import re
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

# ${CONST_PREFIX}_a01_s1_w1506fb051-c2ad-45db-8a52-674278937a31.tif
PATTERN = re.compile(r"(.+)_([a-p]\d{2})_s(\d)_w(.+)\.tif")

ROWS = 16
COLUMNS = 24
FIELDS = 9
CHANNELS = 5

CHANNEL_NAMES = ("Hoechst", "ERSyto", "ERSytoBleed", "PhGolgi", "Mito")
EXTRA_KV = {"ChannelNames": ",".join(CHANNEL_NAMES)}


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    return parser.parse_args(argv[1:])


def consistency_check(by_well):
    assert len(by_well) == ROWS * COLUMNS
    for by_field in by_well.itervalues():
        assert len(by_field) == FIELDS
        for seq in by_field.itervalues():
            assert len(seq) == CHANNELS


def group_files(data_dir):
    d = {}  # well -> field -> fnames
    for name in os.listdir(data_dir):
        if not name.endswith(".tif") or name.startswith("."):
            continue
        head, well, field, channel = PATTERN.search(name).groups()
        d.setdefault(well, {}).setdefault(field, []).append((channel, head))
    return d


def write_screen(data_dir, plate, outf):
    d = group_files(data_dir)
    consistency_check(d)
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS)
    for idx in range(ROWS * COLUMNS):
        r, c = writer.coordinates(idx)
        well = "%s%02d" % (r.lower(), c)
        field_values = []
        by_field = d[well]
        for i in range(FIELDS):
            field = "%d" % (i + 1)
            seq = by_field[field]
            assert len(set(_[1] for _ in seq)) == 1
            head = seq[0][1]
            c_block = "<%s>" % ",".join(_[0] for _ in sorted(seq))
            pattern = "%s_%s_s%s_w%s.tif" % (head, well, field, c_block)
            field_values.append(os.path.join(data_dir, pattern))
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
