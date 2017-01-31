#!/usr/bin/env python
import sys
import tables
h5file = tables.open_file(sys.argv[1], mode="a")
table = h5file.root.OME.Measurements
table.cols.WellID.create_index(
    optlevel=9, _testmode=True, _verbose=True)
h5file.close()
