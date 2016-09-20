#!/usr/bin/env python

"""
Create a map-annotation on a top-level object based on an IDR study file.
Example:

    scripts/annotate_study.py \
        idr-metadata/idr0001-graml-sysgro/idr0001-study.txt Screen:3
"""

import argparse
import pandas as pd

from pyidr.mapannotations import create_map_annotation
# This import needs to come after the above, otherwise there's a mysterious
# "ImportError: cannot import name NamedValue" error
from omero.cli import CLI, ProxyStringType


# Mapping of
# - study keys (from the study file)
# - displayed names
# - displayed values
study_keys = [
    ('Study PubMed ID', 'PubMed ID'),
    ('Study PubMed ID', 'PubMed URL',
     'http://www.ncbi.nlm.nih.gov/pubmed/{{ value }}'),
    ('Study DOI', 'Publication DOI'),
]

ns = 'openmicroscopy.org/idr/study'


def get_pairs(study):
    # The study files are ragged tables, so Pandas will fill in additional
    # cells with NaN.
    df = pd.read_table(study, sep='\t', header=None)

    kvpairs = []
    for items in study_keys:
        key = items[0]
        display = items[1]
        try:
            template = items[2]
        except IndexError:
            template = '{{ value }}'

        rows = df.loc[df[0] == key]
        # TODO: Allow missing?
        if len(rows) != 1:
            raise Exception(
                'Expected 1 row matching %s, found %d' % (key, len(rows)))
        value = template.replace('{{ value }}', rows.iloc[0, 1])
        kvpairs.append((display, value))

    return kvpairs


def run(studyfile, targetstr):
    try:
        # `omero shell --login` automatically creates the client object
        session = client.getSession()
        cli = None
    except NameError:
        cli = CLI()
        cli.loadplugins()
        cli.onecmd('login')
        session = cli.get_client().getSession()

    try:
        us = session.getUpdateService()

        target = ProxyStringType()(targetstr)
        rowkvs = get_pairs(studyfile)
        links = create_map_annotation([target], rowkvs, ns)
        ids = us.saveAndReturnIds(links)
        print 'Created MapAnnotation links: %s' % ids
    finally:
        if cli:
            cli.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('studyfile')
    parser.add_argument('target')
    args = parser.parse_args()
    run(args.studyfile, args.target)


if __name__ == '__main__':
    main()
