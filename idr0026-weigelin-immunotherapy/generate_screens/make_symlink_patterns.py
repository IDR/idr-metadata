#!/usr/bin/env python

import sys
import os
import re
from argparse import ArgumentParser

from pyidr.file_pattern import FilePattern
from common import mkdir_p

# E.g., "12-18-43_PMT - PMT [FD6_FDRED] [00]_Time Time0000.tif" ->
# ('12-18-43_PMT', 'FD6_FDRED', '00', '0000')
PATTERN = re.compile(
    r"(.*?_PMT)\s-\sPMT\s\[(.*?)\]\s\[(\d+)\]_Time\sTime(\d+).tif"
)


def parse_cl(argv):
    parser = ArgumentParser()
    parser.add_argument("dir", metavar="DIR", help="dir")
    parser.add_argument("-o", "--out-dir", metavar="DIR", help="output dir",
                        default=os.getcwd())
    parser.add_argument("-t", "--tag", metavar="STRING", help="base tag")
    return parser.parse_args(argv[1:])


def get_t_block(grouplist):
    timepoints = sorted(set(_[3] for _ in grouplist), key=int)
    assert len(set(len(_) for _ in timepoints)) == 1
    tmin, tmax = timepoints[0], timepoints[-1]
    assert map(int, timepoints) == range(int(tmin), int(tmax) + 1)
    return "<%s-%s>" % (tmin, tmax)


def get_pattern(grouplist):
    # grouplist[i] -> head, ch_str, field, t
    assert len(set(_[0] for _ in grouplist)) == 1
    n_channels = len(set(_[1] for _ in grouplist))
    n_timepoints = len(set(_[3] for _ in grouplist))
    assert len(grouplist) == n_channels * n_timepoints  # (no "holes")
    channel_names = ",".join(set(_[1] for _ in grouplist))
    ch_block = "<%s>" % channel_names
    pattern = "%s - PMT [%s] [%s]_Time Time%s.tif" % (
        grouplist[0][0], ch_block, grouplist[0][2], get_t_block(grouplist)
    )
    return pattern, channel_names


def group_files(data_dir):
    d = {}
    fnames = set()
    for bn in os.listdir(data_dir):
        if not bn.endswith(".tif"):
            continue
        fnames.add(os.path.join(data_dir, bn))
        try:
            groups = head, ch_str, field, t = PATTERN.match(bn).groups()
        except (AttributeError, ValueError):
            sys.stderr.write("unexpected pattern: %s\n" % bn)
        d.setdefault(field, []).append(groups)
    for field_idx, grouplist in d.iteritems():
        pattern, channel_names = get_pattern(grouplist)
        d[field_idx] = (os.path.join(data_dir, pattern), channel_names)
    fnames_from_patterns = set()
    for pattern, _ in d.itervalues():
        fnames_from_patterns |= set(FilePattern(pattern).filenames())
    assert fnames_from_patterns == fnames
    return d


def write_patterns(data_dir, outdir, tag):
    d = group_files(data_dir)
    pairs = []
    for field, (pattern, channel_names) in d.iteritems():
        out_bn = "%s.%s.pattern" % (tag, field)
        pairs.append((field, out_bn))
        out_fn = os.path.join(outdir, out_bn)
        with open(out_fn, "w") as fo:
            fo.write("# ChannelNames = %s\n" % channel_names)
            fo.write("%s\n" % pattern)
    return [_[1] for _ in sorted(pairs)]


def main(argv):
    args = parse_cl(argv)
    if not args.tag:
        args.tag = os.path.basename(os.path.normpath(args.dir))
    mkdir_p(args.out_dir)
    out_bnames = write_patterns(args.dir, args.out_dir, args.tag)
    return out_bnames


if __name__ == "__main__":
    main(sys.argv)
