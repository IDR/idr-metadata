#!/usr/bin/env python

import sys
import os
import re
import operator
from argparse import ArgumentParser

from pyidr.screenio import ScreenWriter

ROWS = 1
COLUMNS = 1

# E.g., "12-18-43_PMT - PMT [FD6_FDRED] [00]_C01_Time Time0000.ome.tif" ->
# ('12-18-43_PMT', 'FD6_FDRED', '00', '01', '0000')
PATTERN = re.compile(
    r"(.*?_PMT)\s-\sPMT\s\[(.*?)\]\s\[(\d+)\]_C(\d+)_Time\sTime(\d+).ome.tif"
)


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--output", metavar="FILE", help="output file")
    parser.add_argument("-p", "--plate", metavar="PLATE", help="plate name")
    return parser.parse_args(argv[1:])


def assert_related_ch(grouplist):
    """
    Verify that channel info is redundant, i.e., a given ch_str is
    always associated to the same ch_n.
    """
    d = {}
    for head, ch_str, field, ch_n, t in grouplist:
        assert d.setdefault(ch_str, ch_n) == ch_n


def get_ch_block(grouplist):
    """
    We can't do e.g. [<BD2_GREEN,FD6_FDRED>] [00]_C0<0-1> because it
    describes two separate dimensions. However, since ch_str and
    ch_n vary together and field is constant, we can merge all three.
    """
    ch_tag_elems = sorted(
        set([_[1:4] for _ in grouplist]),
        key=operator.itemgetter(2)
    )
    ch_tags = ["[%s] [%s]_C%s" % _ for _ in ch_tag_elems]
    ch_block = "<%s>" % ",".join(ch_tags)
    ch_names = [_[0] for _ in ch_tag_elems]
    return ch_block, ch_names


def get_t_block(grouplist):
    timepoints = sorted(set(_[4] for _ in grouplist), key=int)
    assert len(set(len(_) for _ in timepoints)) == 1
    tmin, tmax = timepoints[0], timepoints[-1]
    assert map(int, timepoints) == range(int(tmin), int(tmax) + 1)
    return "<%s-%s>" % (tmin, tmax)


def get_pattern(grouplist):
    # grouplist[i] -> head, ch_str, field, ch_n, t
    assert len(set(_[0] for _ in grouplist)) == 1
    n_channels = len(set(_[3] for _ in grouplist))
    n_timepoints = len(set(_[4] for _ in grouplist))
    assert len(grouplist) == n_channels * n_timepoints  # (no "holes")
    assert_related_ch(grouplist)
    ch_block, ch_names = get_ch_block(grouplist)
    return "%s - PMT %s_Time Time%s.ome.tif" % (
        grouplist[0][0], ch_block, get_t_block(grouplist)
    ), ch_names


def group_files(data_dir):
    d = {}
    for bn in os.listdir(data_dir):
        if not bn.endswith(".tif"):
            continue
        try:
            groups = head, ch_str, field, ch_n, t = PATTERN.match(bn).groups()
        except (AttributeError, ValueError):
            sys.stderr.write("unexpected pattern: %s\n" % bn)
        d.setdefault(int(field), []).append(groups)
    ch_sets = []
    for field_idx, grouplist in d.iteritems():
        pattern, ch_names = get_pattern(grouplist)
        d[field_idx] = pattern
        ch_sets.append(ch_names)
    assert len(set(tuple(_) for _ in ch_sets)) == 1
    return d, ch_sets[0]


def write_screen(data_dir, plate, outf):
    d, ch_names = group_files(data_dir)
    extra_kv = {"AxisTypes": "CT", "ChannelNames": ",".join(ch_names)}
    n_fields = len(d)
    writer = ScreenWriter(plate, ROWS, COLUMNS, n_fields)
    assert ROWS == COLUMNS == 1
    field_values = []
    for field_idx in sorted(d):
        field_values.append(os.path.join(data_dir, d[field_idx]))
    writer.add_well(field_values, extra_kv=extra_kv)
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
