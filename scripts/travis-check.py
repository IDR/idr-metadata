#!/usr/bin/env python

"""
Recursively checks YAML and CSV files for validity

YAML docs should contain a single document
CSVs should have unique column names and be loadable with pandas
"""

import os
import pandas
import yaml

# list files to exclude from checks as relative paths from the repository root
EXCLUDE = frozenset([
    "idr0027-dickerson-chromatin/experimentA/idr0027-AnalysisAllData.csv"
])
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)
EXCLUDE = [os.path.normpath(os.path.join(REPO_ROOT, _)) for _ in EXCLUDE]


for root, dirs, files in os.walk(REPO_ROOT):
    for f in files:
        fn = os.path.join(root, f)
        if fn in EXCLUDE:
            continue

        if fn.lower().endswith('.yml') or fn.lower().endswith('.yaml'):
            print fn
            docs = list(yaml.load_all(f))
            assert len(docs) == 1

        if fn.lower().endswith('.csv'):
            print fn
            # pandas is way too tolerant of extra columns- they may be treated
            # as a single or multi row index, or discarded. Since we don't
            # use index columns the following seems to be the best way of
            # checking none of the columns have been converted to an index.
            # Unfortunately error messages may not be very helpful.
            # This will also check for duplicate columns, `mangle_dupe_cols`
            # means the column names will be different.
            df_default = pandas.read_csv(fn)
            df = pandas.read_csv(fn, index_col=False, mangle_dupe_cols=False)
            pandas.util.testing.assert_frame_equal(df_default, df)
            for c in df.columns:
                assert not c.startswith('Unnamed:'), \
                    'Unnamed column found'
