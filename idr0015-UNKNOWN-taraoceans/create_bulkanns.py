#!/usr/bin/env python

"""
Create a bulk annotations CSV file from the original XLSX files
"""

import numpy as np
import pandas as pd
import re


def get_sections(df):
    """
    Split into sections indicated by //.*, remove empty rows
    """
    dfd = df.dropna(how='all')
    secheads = [re.match('//(.*)', s) for s in dfd.iloc[:, 0]]
    indheads = np.where(secheads)[0]

    sections = {}
    for n in range(len(indheads)):
        secname = secheads[indheads[n]].group(1)
        try:
            r = range(indheads[n] + 1, indheads[n + 2])
        except IndexError:
            r = range(indheads[n] + 1, dfd.shape[0])

        assert secname not in sections, 'Multiple "%s" found' % secname
        sections[secname] = dfd.iloc[r, :]

    return sections


def load_metadata(xlsin):
    df = pd.read_excel(xlsin)
    sections = get_sections(df)
    metadata = sections['METADATA']

    # Use the first row of the section as the header
    metadata.columns = metadata.iloc[0, :]
    metadata = metadata.iloc[1:, :]
    return metadata


def save_csv(df, csvout):
    df.to_csv(csvout, index=False, encoding='utf-8')
    print('Saved %s' % csvout)


def merge_columns(acquisitions, samples, joincol):
    """
    Combine the acquisition and sample metadata.
    There are more samples than acquisitions, so join on the acquisitions.
    Verify that common columns contain the same values.
    """
    common = list(sorted(set(acquisitions.columns).intersection(
        samples.columns)))
    duptag = '<MERGED_SAMPLE>'

    merged = acquisitions.merge(
        samples, how='left', on=joincol, sort=True, suffixes=('', duptag))

    for c in common:
        if c == joincol:
            continue
        v = merged[c] == merged[c + duptag]
        if sum(v) != len(v):
            raise Exception(
                'Mismatch between acquisitions and samples "%s"' % c)

    dupcols = [c for c in merged.columns if c.endswith(duptag)]
    print('Dropping %d duplicate columns: %s' % (len(dupcols), dupcols))
    merged.drop(dupcols, axis=1, inplace=True)
    return merged


def add_omero_columns(metadata, omeromap):
    """
    Append columns required by OMERO for linking to the imported data
    Keep the original column names so that the original metadata is unchanged
    """
    for k, v in omeromap.iteritems():
        assert v not in metadata.columns
        metadata[v] = metadata[k]
    return metadata


def run(acquisitions_xls, samples_xls, outputstem=None, intermediates=False):
    joincol = 'HTM_SAMPLE_LABEL_aggregated'
    omeromap = {
        'HTM_ACQUISITION_Run_Label': 'Plate',
        'HTM_ACQUISITION_Sample_WellCoordinates': 'Well',
    }

    acquisitions = load_metadata(acquisitions_xls)
    samples = load_metadata(samples_xls)

    if outputstem and intermediates:
        save_csv(acquisitions, '%sacquisitions.csv' % outputstem)
        save_csv(samples, '%ssamples.csv' % outputstem)

    merged = merge_columns(acquisitions, samples, joincol)
    bulkanns = add_omero_columns(merged, omeromap)

    if outputstem:
        save_csv(bulkanns, '%sBULK_ANNOTATION.csv' % outputstem)

    # return acquisitions, samples, bulkanns
    return bulkanns


if __name__ == '__main__':
    acquisitions_xls = 'HTM_ACQUISITIONS_REGISTRY_TARA_HCS1_H5.xlsx'
    samples_xls = 'HTM_SAMPLES_REGISTRY_TARA_HCS1.xlsx'
    run(acquisitions_xls, samples_xls, 'taraoceans.', False)
