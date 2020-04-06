#!/usr/bin/env python

"""\
Screen generator for idr0035. The dataset is described at
https://data.broadinstitute.org/bbbc/BBBC021

The structure is the following:

  <PLATE>/<FIXED_PART>_<WELL>_s<FIELD>_w<CHANNEL><UUID4>.tif

E.g.:

  Week1_22123/Week1_150607_B02_s1_w107447158-AC76-4844-8431-E6A954BD1174.tif
"""

import sys
import os
import re
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

ROWS = 8
COLUMNS = 12
FIELDS = 4
CHANNEL_NAMES = "DAPI", "Tubulin", "Actin"
EXTRA_KV = {
    "AxisTypes": "C",
    "ChannelNames": ",".join(CHANNEL_NAMES),
}

PATTERN = re.compile(r"(.*)([A-H]\d{2})_s([1-4])_w(.+)\.tif")


def get_patterns(subd):
    """
    Get the well-to-fields-to-patterns map for a subdirectory.
      {'B02':
        {1: 'Week1_150607_B02_s1_w<...>.tif'
         ...
         4: 'Week1_150607_B02_s4_w<...>.tif'}
       ...
      }
    """
    exp_fields = frozenset(range(1, 5))
    exp_channels = frozenset(["1", "2", "4"])
    d = {}
    for bn in os.listdir(subd):
        fn = os.path.join(subd, bn)
        try:
            head, well, field, channel = PATTERN.match(bn).groups()
            field = int(field)
        except (AttributeError, ValueError):
            raise RuntimeError("Unexpected file name: %r" % (fn))
        d.setdefault(well, {}).setdefault(field, set()).add(channel)
    for well, field_map in d.iteritems():
        assert set(field_map) == exp_fields
        for field, channels in field_map.iteritems():
            assert set(_[0] for _ in channels) == exp_channels
            field_map[field] = "%s%s_s%d_w<%s>.tif" % (
                head, well, field, ",".join(sorted(channels))
            )
    return d


def write_screen(data_dir, plate, outf, screen=None):
    kwargs = {"screen_name": screen} if screen else {}
    patterns = get_patterns(data_dir)
    writer = ScreenWriter(plate, ROWS, COLUMNS, FIELDS, **kwargs)
    for idx in range(ROWS * COLUMNS):
        well_tag = "%s%02d" % writer.coordinates(idx)
        try:
            field_map = patterns[well_tag]
        except KeyError:
            writer.add_well([])
            continue
        field_values = []
        for i in range(1, FIELDS + 1):
            field_values.append(os.path.join(data_dir, field_map[i]))
        writer.add_well(field_values, extra_kv=EXTRA_KV)
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
