#!/usr/bin/env python

import sys
import os
import re
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

SUBD_PATTERN = re.compile(r"plate \d ([AE])(\d+)")
NAME_PATTERN = re.compile(r"V (\d)_X (\d)_Y (\d)")
CH_PATTERN = re.compile(r"^(.*)_ch0(\d).tif")
EXPECTED_FIELDS = [(0, 0), (0, 1), (1, 0), (1, 1)]  # X, Y values

ROWS = 8
COLUMNS = 12
FIELDS = 4
EXCLUDE_READERS = ["loci.formats.in.TCSReader"]


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    return parser.parse_args(argv[1:])


def consistency_check(d):
    if len(d) != ROWS * COLUMNS:
        writer = ScreenWriter("foo", ROWS, COLUMNS, FIELDS)
        missing = []
        for idx in range(ROWS * COLUMNS):
            k = writer.index2d(idx)
            if k not in d:
                missing.append(k)
        print("ERROR: missing well(s):", missing)
    for v in d.itervalues():
        assert set(v) == set(EXPECTED_FIELDS)


def group_files(data_dir):
    d = {}  # well -> field -> fnames
    for bn in os.listdir(data_dir):
        row_group, column = SUBD_PATTERN.match(bn).groups()
        column = int(column) - 1
        subd = os.path.join(data_dir, bn, "Sequence", "Loop_ 0")
        for name in os.listdir(subd):
            if not name.endswith(".tif"):
                continue
            row, x, y = map(int, NAME_PATTERN.search(name).groups())
            # --- Override indices according to subdir name ---
            if row_group == 'A' and 4 <= row <= 7:
                row -= 4
            if row_group == 'E' and 0 <= row <= 3:
                row += 4
            # --- Adjust for REVERSED ORDER cases -------------
            if "REVERSED ORDER" in bn:
                if 4 <= row <= 7:
                    row = 11 - row
                if 0 <= row <= 3:
                    row = 3 - row
            # -------------------------------------------------
            well = d.setdefault((row, column), {})
            field = well.setdefault((x, y), [])
            field.append(os.path.join(subd, name))
    return d


def build_pattern(fnames):
    """\
    Build file patterns for each field.

    Author stated: "in cases with 4 channels one of them is empty.
    ch0 = DAPI, ch01 = empty, ch02 = HPA and ch03 = microtubules".
    """
    n_channels = len(fnames)
    assert n_channels > 0
    assert len(set(os.path.dirname(_) for _ in fnames)) == 1
    dirname = os.path.dirname(fnames[0])
    bnames = [os.path.basename(_) for _ in fnames]
    groups = [CH_PATTERN.match(_).groups() for _ in bnames]
    assert len(set(_[0] for _ in groups)) == 1
    head = groups[0][0]
    assert set(int(_[1]) for _ in groups) == set(range(n_channels))
    assert 3 <= n_channels <= 4
    if n_channels > 3:
        block = "<0,2,3>"
    else:
        block = "<0-%d>" % (n_channels - 1)
    return os.path.join(dirname, "%s_ch0%s.tif" % (head, block))


def write_screen(data_dir, plate, outf):
    d = group_files(data_dir)
    consistency_check(d)
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS,
                          exclude_readers=EXCLUDE_READERS)
    for idx in range(ROWS * COLUMNS):
        well_coords = writer.index2d(idx)
        field_values = []
        try:
            by_field = d[well_coords]
        except KeyError:
            sys.stderr.write("missing well: %r\n" % (well_coords,))
        else:
            for i, field_coords in enumerate(EXPECTED_FIELDS):
                field_values.append(build_pattern(by_field[field_coords]))
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
