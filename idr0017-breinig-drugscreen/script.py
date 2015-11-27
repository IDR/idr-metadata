#!/usr/bin/env python

from glob import glob
from os import mkdir
from os import remove
from os import symlink
from os.path import abspath
from os.path import basename
from os.path import exists
from os.path import islink

# jamoore@necromancer /ome/data_repo/from_IDR/screen/pgpc/2011-11-17_X-Man_LOPAC_X01_LP_S01_1 $ cat test.screen
PLATE = """[Plate]
Name = %s
Rows = 16
Columns = 20
Fields = 4
"""

WELL = """[Well %(count)s]
Row = %(irow)s 
Column = %(icol)s
Field_0 = %(crow)s - %(ccol)s(fld 1 wv c<0-1>).tif
Field_1 = %(crow)s - %(ccol)s(fld 2 wv c<0-1>).tif
Field_2 = %(crow)s - %(ccol)s(fld 3 wv c<0-1>).tif
Field_3 = %(crow)s - %(ccol)s(fld 4 wv c<0-1>).tif
"""

DIR="../20151124/14_X-Man_10x/source/"

for x in glob(DIR+"*"):
    d = basename(x)
    if not exists(d):
        mkdir(d)
    out = open(d + "/test.screen", "w")
    print >>out, PLATE % d
    count = 0

    try:
        letters = "ABCDEFGHIJKLMNOP"
        for row in letters:
            for col in range(1, 25):
                print d, row, col
                data = {
                    "count": count,
                    "crow": row,
                    "ccol": col,
                    "irow": letters.index(row),
                    "icol": col - 1,
                }
                print >>out,  WELL % data
                count += 1
                for fld in range(1, 5):
                    for idx, ch in enumerate(("DAPI", "Cy3")):
                        source = x + "/%s - %s(fld %s wv %s - %s).tif" % (row, col, fld, ch, ch)
                        source = abspath(source)
                        if not exists(source):
                            raise Exception(source)
                        target = d + "/%s - %s(fld %s wv c%s).tif" % (row, col, fld, idx)
                        if islink(target):
                            remove(target)
                        symlink(source, target)
    finally:
        out.close()
