#!/usr/bin/env python

from pyidr import file_pattern as fp
from glob import glob
from os.path import basename


base = "/uod/idr/filesets/idr0010-doil-dnadamage/"
base += "20150501-original/Restored GW screen/"
plates = "idr-metadata/idr0010-doil-dnadamage/screenA/plates/"
dirs = glob(base + "/*")


def iglob(pattern):
    def either(c):
        return '[%s%s]' % (c.lower(), c.upper()) if c.isalpha() else c
    return glob(''.join(map(either, pattern)))


for dir in dirs:
    try:
        dapi, = [x for x in iglob(dir + "/*dapi*") if "spot" not in x]
        try:
            bp, = [x for x in iglob(dir + "/*bp*") if "spot" not in x]
        except Exception:  # Try BB
            bp, = [x for x in iglob(dir + "/*bb*") if "spot" not in x]
    except Exception:
        raise Exception(dir)

    plate = basename(dir)
    bp = bp.replace("bp", "bxxx")
    rv = fp.find_pattern_2seq(dapi, bp)
    rv = rv.replace("bxxx", "bp")
    print(plate, " ".join(rv.split("/")[-1].split(" ")[1:]))
    with open("%s/%s" % (plates, plate), "w") as screen_file:
        screen_file.write("%s/%s.pattern\n" % (plates, plate))
    with open("%s/%s.pattern" % (plates, plate), "w") as pattern_file:
        pattern_file.write(rv)
