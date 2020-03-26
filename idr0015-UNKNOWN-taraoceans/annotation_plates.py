#!/usr/bin/env python

import omero
from omero.cli import cli_login
from omero.rtypes import unwrap
import pandas as pd
import re
import warnings


with cli_login() as cli:

    client = cli.get_client()

    bulkcsv = 'taraoceans.BULK_ANNOTATION.csv'
    screenid = 1201

    ignore_missing = True

    ns = omero.constants.namespaces.NSBULKANNOTATIONS

    qs = client.getSession().getQueryService()  # noqa
    us = client.getSession().getUpdateService()  # noqa

    df = pd.read_csv(bulkcsv)

    q = ('SELECT spl.child.id, spl.child.name FROM ScreenPlateLink spl '
         'WHERE spl.parent.id=%d' % screenid)
    rs = unwrap(qs.projection(q, None))

    class PlateInfo:

        def __init__(self, i, platename):
            self.i = i
            self.name, u, v = re.match(
                r'([\w_-]+)_chamber--(U\d\d)--(V\d\d)', r[1]).groups()
            if not ("%s%s%s" % (self.name, u, v)).strip():
                raise Exception(r[1])
            self.well = "%s%s" % (u, v)

        def __str__(self):
            return "%s: %s--%s" % (self.i, self.name, self.well)

    plateinfos = [PlateInfo(r[0], r[1]) for r in rs]
    assert len(plateinfos) == 84  # As of Jun 2017

    names_csv = set(df['Plate'])
    names_run = set(pm.name for pm in plateinfos)
    # Check all plates have an entry in the CSV
    missing = names_run.difference(names_csv)
    if missing:
        # msg = 'No matching plates found for:%s\n' % ('\n'.join(missing))
        msg = "No matching plate/wells found for", len(missing)
        if ignore_missing:
            warnings.warn(msg)
        else:
            raise Exception(msg)

    missing2 = []
    links = []
    # print df[["Plate", "Well"]].to_csv(sep="\t", index=False)
    for pm in plateinfos:

        if pm.name in missing:
            continue

        r = df.loc[(df['Plate'] == pm.name) & (df['Well'] == pm.well), :]
        target = omero.model.PlateI(pm.i, False)
        rowkvs = zip(r.columns, r.values.squeeze())

        if len(rowkvs) == 0:
            missing2.append("%s // %s" % (pm.name, pm.well))
            continue

        # Copy from new _create_cmap_annotation
        # link = BulkToMapAnnotationContext.create_map_annotation(
        #     [target], rowkvs, ns)

        NamedValue = omero.model.NamedValue
        ma = omero.model.MapAnnotationI()
        ma.setNs(omero.rtypes.rstring(ns))
        mv = []
        for k, vs in rowkvs:
            if not isinstance(vs, (tuple, list)):
                vs = [vs]
            for v in vs:
                if str(v) != "http://":  # Filter
                    mv.append(NamedValue(k, str(v)))

        ma.setMapValue(mv)
        link = omero.model.PlateAnnotationLinkI()
        link.parent = target
        link.child = ma
        links.append(link)

    if missing2:
        msg = "No matching plate/wells found for", len(missing2)
        if ignore_missing:
            warnings.warn(msg)
        else:
            raise Exception(msg)

    ids = us.saveAndReturnIds(links)
    print('Created MapAnnotation links: %s' % len(links))
