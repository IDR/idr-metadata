#!/usr/bin/env python

import pandas
import numpy as np
import omero
import omero.clients
import omero.gateway
from omero.rtypes import rstring
import yaml


class ProgressRecord(object):

    def __init__(self, filename):
        self.filename = filename
        self.cache = {}
        try:
            with open(self.filename, 'r') as f:
                for line in f:
                    id, state = line.split(':', 1)
                    self._setcache(id.strip(), state.strip())
        except IOError:
            print 'File not found: %s' % self.filename
            # Assume this means file doesn't exist
            pass

    def _setcache(self, id, state):
        try:
            self.cache[str(id)].append(state)
        except KeyError:
            self.cache[str(id)] = [state]

    def set(self, id, state):
        with open(self.filename, 'a') as f:
            f.write('%s:%s\n' % (id, state))
        self._setcache(id, state)

    def get(self, id):
        return self.cache.get(str(id), [])


def connect(h, u, p, **kwargs):
    props = {}
    if 'proxy' in kwargs:
        proxy = kwargs['proxy']
        if 'host' in proxy:
            props['Ice.SOCKSProxyHost'] = proxy['host']
        if 'port' in proxy:
            props['Ice.SOCKSProxyPort'] = proxy['port']
    client = omero.client(h, props)
    session = client.createSession(u, p)
    return client, session


def config(f):
    with open(f) as h:
        y = yaml.load(h)
    return y


def load_features(f, metadatacols=None, roicol=None, **kwargs):
    # Autoconvert all except metddata columns which are explicitly typed
    dtypes = dict(kv for m in metadatacols for kv in m.iteritems())
    colnames = [k for m in metadatacols for k in m.keys()]
    df = pandas.read_table(f, dtype=dtypes, **kwargs)

    assert all(m in df.columns for m in colnames)
    selmeta = [(c in colnames and c != roicol) for c in df.columns]
    selvals = [(c not in colnames and c != roicol) for c in df.columns]

    dfmeta = df.iloc[:, selmeta]
    dfvals = df.iloc[:, selvals]
    if roicol:
        dfroi = df[roicol]
    else:
        dfroi = None
    dfvals = dfvals.convert_objects(convert_numeric=True)
    return dfmeta, dfvals, dfroi


def parse_coords(coordstr):
    assert coordstr[0] == '['
    assert coordstr[-1] == ']'
    points = []
    for c in coordstr[1:-1].split(';'):
        points.append(tuple(int(p) for p in c.split()))
    return points


def create_roi(coordstr, imageid):
    points = parse_coords(coordstr)
    poly = omero.model.PolygonI()
    pointstr = ' '.join('%d,%d' % p for p in points)
    poly.setPoints(rstring(pointstr))
    roi = omero.model.RoiI()
    roi.addShape(poly)
    im = omero.model.ImageI(imageid, False)
    roi.setImage(im)
    print 'create_roi %s... %s' % (points[:3], imageid)
    return roi


def update(obj, session):
    us = session.getUpdateService()
    return us.saveAndReturnObject(obj)


def create_feature(ms, vs):
    print 'create_feature %s %s...' % (ms.values, vs[:3].values)


#####


cfg = config('input.yml')
dfmeta, dfvals, dfroi = load_features(
    cfg['features'], cfg['metadatacolumns'], cfg['roicolumn'], nrows=1000)
print dfmeta.dtypes.to_string()
print dfvals.dtypes.to_string()
print dfroi.dtypes
print cfg

assert dfroi is not None
scfg = cfg['server']
proxy = scfg.get('socksproxy', {})
client, session = connect(
    scfg['host'], scfg['user'], scfg['password'], proxy=proxy)

dfmeta.insert(0, 'RoiID', np.int64(0))
print dfmeta.dtypes.to_string()

p = ProgressRecord(cfg['progresslist'])
for i in xrange(dfmeta.shape[0]):
    print 'Row', i
    if 'r' not in p.get(i):
        roi = create_roi(dfroi.iloc[i], -1)
        p.set(i, 'r')
    if 'f' not in p.get(i):
        ft = create_feature(dfmeta.iloc[i], dfvals.iloc[i])
        p.set(i, 'f')
