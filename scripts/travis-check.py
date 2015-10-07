#!/usr/bin/env python

"""
Recursively checks YAML and CSV files for validity

YAML docs should contain a single document
CSVs should have unique column names and be loadable with pandas
"""

import os
import pandas
import sys
import yaml


for root, dirs, files in os.walk(sys.argv[1]):
    for f in files:
        fn = os.path.join(root, f)

        if fn.lower().endswith('.yml') or fn.lower().endswith('.yaml'):
            print fn
            docs = list(yaml.load_all(f))
            assert len(docs) == 1

        if fn.lower().endswith('.csv'):
            print fn
            df = pandas.read_csv(fn, index_col=False, mangle_dupe_cols=False)
            assert len(set(df.columns)) == len(df.columns), \
                'Duplicate columns found'
            for c in df.columns:
                assert not c.startswith('Unnamed:'), \
                    'Unnamed column found'
