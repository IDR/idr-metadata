#!/usr/bin/env python

from argparse import ArgumentParser
from os.path import basename
from glob import glob
from re import compile

ROWS = 22 # Y
COLUMNS = 18 # X
PLATE = """[Plate]
Name = Tara
Rows = %s
Columns = %s
Fields = 1""" % (ROWS, COLUMNS)

WELL = """
[Well %(well)s]
Row = %(row)s 
Column = %(col)s"""

parser = ArgumentParser()
parser.add_argument("file", nargs="+")
ns = parser.parse_args()

well_map = {}
def make_well_map2():
    c = -1
    for y in range(ROWS):
        for x in range(COLUMNS):
            c += 1  
            well_map["%s-%s" % (x, y)] = c
make_well_map2()

pat = compile(".*image--L(\d+)--S(\d+)--U(\d+)--V(\d+)--J(\d+)--E(\d+)--O(\d+)--X(\d+)--Y(\d+)--T(\d+).*")

print PLATE
for y in range(0, ROWS):
	for x in range(0, COLUMNS):
		found = None
		f1 = "field--X%02d--Y%02d" % (x, y)
		for f2 in ns.file:
			if f2.endswith(f1):
				found = f2
				break


		print WELL % {
			"well": well_map["%s-%s" % (x, y)],
			"col": x,
			"row": y,
		}

		if found:
			images = glob(found + "/image*")
			first = images.pop(0)
			m = pat.match(first)
			if not m: raise Exception(first)
			L = int(m.group(1))
			S = int(m.group(2))
			U = int(m.group(3))
			V = int(m.group(4))
			J = int(m.group(5))
			E = int(m.group(6))
			O = int(m.group(7))
			T = int(m.group(10))
			# Check others here

			stuff = "%02d--".join(["L", "S", "U", "V", "J", "E", "O", "X", "Y", "T"])
			stuff = "%%s/image--%s%%02d--Z<00-19>--C<00-04>.ome.tif" % stuff
			path = stuff % (found, L, S, U, V, J, E, O, x, y, T)
			print "Field_0 = %s" % path
