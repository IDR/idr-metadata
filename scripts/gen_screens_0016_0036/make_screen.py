#!/usr/bin/env python

"""\
Screen generator for idr0016. The root directory has a subdirectory
for each plate and channel, encoded as <PLATE>-<CHANNEL>:

  24278-ERSyto
  [...]
  24278-Ph_golgi
  24279-ERSyto
  [...]

Each subdirectory contains TIFF files for all wells and fields,
encoded as <FIXED_TAG>_<WELL_TAG>_<FIELD_TAG>_<UUID4>.tif, where
WELL_TAG is the same for the whole subdirectory, WELL_TAG ranges from
a01 to p24 and FIELD_TAG ranges from s1 to s6:

  cdp2bioactives_a01_s1_w2edcec6dc-b1e3-4ffc-80da-9b049a89447b.tif
  [...]
  cdp2bioactives_a01_s6_w226769d39-9e39-46fe-91c9-114d83d88293.tif
  cdp2bioactives_a02_s1_w27ea828eb-0507-4427-99be-08a3e4d682f7.tif
  [...]
  cdp2bioactives_p24_s6_w2a2bb6fea-13ae-4645-ae08-ef64ae92c281.tif
"""

import sys
import os
import re
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

ROWS = 16
COLUMNS = 24
EXTRA_KV = {
    "AxisTypes": "C",
}


FIELD_TAG_PATTERN = re.compile(r"s(\d+)")


def get_channel_map(data_dir):
    """
    Get the plate-to-channels map from the root dir:

      {'24278': ['ERSyto', ...], '24279': ['ERSyto', ...], ...}

    Each channel list in the returned dictionary is sorted.
    """
    channel_map = {}
    for subd in os.listdir(data_dir):
        if not os.path.isdir(os.path.join(data_dir, subd)):
            continue
        plate_tag, channel_tag = subd.strip().split("-")
        channel_map.setdefault(plate_tag, []).append(channel_tag)
    for v in channel_map.itervalues():
        v.sort()
    return channel_map


def get_file_map(subd):
    """
    Get the well-to-files map for a subdirectory. Convert well tags to
    uppercase so that they match with those provided by ScreenWriter.
    Also, return the number of fields as the largest field index
    across all files in the subdirectory.

      {'A01': [
         'cdp2bioactives_a01_s1_w2edcec6dc-b1e3-4ffc-80da-9b049a89447b.tif',
         ...
         'cdp2bioactives_a01_s6_w226769d39-9e39-46fe-91c9-114d83d88293.tif',
       ...
       'P24': [
         'cdp2bioactives_p24_s1_w249dbc2b4-83ed-4ccc-a782-b3e49b1b6c2c.tif',
         ...
         'cdp2bioactives_p24_s6_w2a2bb6fea-13ae-4645-ae08-ef64ae92c281.tif'
       ]}

    Each file list is sorted wrt field index (s1, s2, ...).
    """
    file_map = {}
    last_field_indices = []
    for fn in os.listdir(subd):
        parts = fn.split("_", 3)
        well_tag, field_tag = parts[1:3]
        well_tag = well_tag.strip().upper()
        m = FIELD_TAG_PATTERN.match(field_tag.strip())
        if m is None:
            sys.stderr.write(
                "WARNING: can't detect field idx for %s\n" %
                os.path.join(subd, fn)
            )
            continue
        field_idx = int(m.groups()[0])
        file_map.setdefault(well_tag, []).append((field_idx, fn))
    for k, v in file_map.iteritems():
        v.sort()
        last_field_indices.append(v[-1][0])
        file_map[k] = [_[1] for _ in v]
    return file_map, max(last_field_indices)


def write_screen(data_dir, plate, outf, screen=None):
    kwargs = {"screen_name": screen} if screen else {}
    channel_map = get_channel_map(data_dir)
    try:
        channel_tags = channel_map[plate]
    except KeyError:
        raise ValueError("Plate %r not found" % (plate,))
    file_maps = {}
    n_fields = []
    for c in channel_tags:
        subd = os.path.join(data_dir, "%s-%s" % (plate, c))
        file_maps[c], nf = get_file_map(subd)
        n_fields.append(nf)
    n_fields = max(n_fields)
    base_path = os.path.join(data_dir, "%s-" % plate)
    writer = ScreenWriter(plate, ROWS, COLUMNS, n_fields, **kwargs)
    for idx in xrange(ROWS * COLUMNS):
        well_tag = "%s%02d" % writer.coordinates(idx)
        if not any(well_tag in file_maps[_] for _ in channel_tags):
            sys.stderr.write(
                "WARNING: plate %s: missing well: %s\n" % (plate, well_tag)
            )
            writer.add_well([])
            continue
        field_values = []
        for i in xrange(n_fields):
            try:
                fnames = [file_maps[_][well_tag][i] for _ in channel_tags]
            except IndexError:
                sys.stderr.write(
                    "WARNING: plate %s: missing field for well %s: %d\n" %
                    (plate, well_tag, i)
                )
            else:
                split_fnames = [os.path.splitext(_) for _ in fnames]
                assert len(set(_[1] for _ in split_fnames)) == 1
                ext = split_fnames[0][1]
                elems = [os.path.join(c, t[0])
                         for (c, t) in zip(channel_tags, split_fnames)]
                field_values.append(
                    "%s<%s>%s" % (base_path, ",".join(elems), ext)
                )
        if len(field_values) == n_fields:
            extra_kv = EXTRA_KV.copy()
            extra_kv['ChannelNames'] = ",".join(channel_tags)
            writer.add_well(field_values, extra_kv=extra_kv)
        else:
            # treat wells with less than n_fields as missing
            writer.add_well([])
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
