#!/usr/bin/env python

# Rename directories from BBBC022 to match the CellImageLibrary format
# Zips downloaded from http://www.cellimagelibrary.org/pages/project_20269
#   are named [PLATEID]-[CHANNEL]
# Zips from https://www.broadinstitute.org/bbbc/BBBC022/ are named
#   BBBC022_v1_images_[PLATEID]w[1-5]

import glob
import os
import pandas
import re

# CSV contains a few rows with too few or too many fields
df0 = pandas.read_csv('BBBC022_v1_image.csv', nrows=0)
df = pandas.read_csv('BBBC022_v1_image.csv',
                     names=(list(df0.columns)+['x1', 'x2']), skiprows=1)


# Verify that the BBBC022 image indicies match
def unique_ws(filenames):
    return set(z.group(1) for z in (re.match(r'IXMtest_\w{3}_\w{2}_w(\d)', f)
               for f in filenames))


assert unique_ws(df.Image_FileName_OrigHoechst) == set({'1'})
assert unique_ws(df.Image_FileName_OrigER) == set({'2'})
assert unique_ws(df.Image_FileName_OrigSyto) == set({'3'})
assert unique_ws(df.Image_FileName_OrigPh_golgi) == set({'4'})
assert unique_ws(df.Image_FileName_OrigMito) == set({'5'})

# Inspection of the image names (w(\d) component) suggests the mapping below
# E.g. IXMtest_P23_s1_w2227537B3-6004-4D7C-9992-EC22DFA440D1.tif
#                     ^^
# Note that columns Image_FileName_OrigER and Image_FileName_OrigSyto in
# BBBC022_v1_image.csv appear to be called ERSyto and ERSytoBleed in
# cellimagelibrary
wmap = {
    1: 'Hoechst',
    2: 'ERSyto',
    3: 'ERSytoBleed',
    4: 'Ph_golgi',
    5: 'Mito',
}
for w in [1, 2, 3, 4, 5]:
    ds = glob.glob('BBBC022_v1_images_?????w%d' % w)
    for d in ds:
        print(d, '%s-%s' % (d[18:23], wmap[w]))
        os.rename(d, '%s-%s' % (d[18:23], wmap[w]))
