#!/usr/bin/env python

import getpass
import pandas
import numpy as np
import omero
import omero.clients
import omero.gateway
from omero.rtypes import rstring, unwrap
import re
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


class SPW(object):

    def __init__(self, session, screenid):
        self.qs = session.getQueryService()
        self.screenid = screenid
        self.plates = {}
        self.fetch(screenid)

    def fetch(self, screenid):
        for plateid, platename in self.get_plates(screenid):
            self.plates[platename] = {'id': plateid}
            acquisitions = {}
            for acqid, acqname in self.get_plate_acquisitions(plateid):
                acq = {'id': acqid}
                wells = {}
                for wid, wrow, wcol, iid, iname in \
                        self.get_wellsamples_and_images(acqid):
                    wells[(wrow, wcol)] = {
                        'wid': wid, 'iid': iid, 'iname': iname}
                acq['wells'] = wells
                acquisitions[acqname] = acq
            self.plates[platename]['acquisitions'] = acquisitions

    def projection(self, q, id, nowrap=True):
        params = omero.sys.ParametersI()
        params.addId(id)
        rs = self.qs.projection(q, params)
        if nowrap:
            return unwrap(rs)
        return rs

    def get_plates(self, screenid):
        rs = self.projection(
            'SELECT spl.child.id, spl.child.name FROM ScreenPlateLink spl '
            'WHERE spl.parent.id=:id', screenid)
        return sorted(rs)

    def get_plate_acquisitions(self, plateid):
        rs = self.projection(
            'SELECT p.id, p.name FROM PlateAcquisition p WHERE p.plate.id=:id',
            plateid)
        return sorted(rs)

    def get_wellsamples_and_images(self, acquisitionid):
        rs = self.projection(
            'SELECT ws.well.id, ws.well.row, ws.well.column, '
            'ws.image.id, ws.image.name FROM WellSample ws '
            'WHERE ws.plateAcquisition.id=:id', acquisitionid)
        return sorted(rs)

    def print_all(self):
        for pk, pv in sorted(self.plates.iteritems()):
            print '[Plate %d] %s' % (pv['id'], pk)
            for ak, av in sorted(pv['acquisitions'].iteritems()):
                print '  [PlateAcquisition %d] %s' % (av['id'], ak)
                for wk, wv in sorted(av['wells'].iteritems()):
                    print '    [Well %d %02d,%02d] [Image %d] %s' % (
                        wv['wid'], wk[0], wk[1], wv['iid'], wv['iname'])

    def coord2offset(self, coord):
        ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        m = re.match('([A-Z]+)([0-9]+)$', coord)
        assert m
        ra, ca = m.groups()
        r = 0
        for a in ra:
            r = r * 26 + ALPHA.find(a) + 1
        c = int(ca)
        return r - 1, c - 1

    def get_image(self, platename, acqname, coord):
        r, c = self.coord2offset(coord)
        wellim = self.plates[platename]['acquisitions'][acqname]['wells'][
            (r, c)]
        return wellim['iid']


def connect(h, u, p, **kwargs):
    props = {}
    if 'proxy' in kwargs:
        proxy = kwargs['proxy']
        if 'host' in proxy:
            props['Ice.SOCKSProxyHost'] = proxy['host']
        if 'port' in proxy:
            props['Ice.SOCKSProxyPort'] = proxy['port']
    client = omero.client(h, props)
    if not p:
        p = getpass.getpass('\nEnter password for user %s: ' % u)
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


def get_dataframe(cfg, **kwargs):
    dfmeta, dfvals, dfroi = load_features(
        cfg['features'], cfg['metadatacolumns'], cfg['roicolumn'], **kwargs)
    print dfmeta.dtypes.to_string()
    print dfvals.dtypes.to_string()
    print dfroi.dtypes
    print cfg

    assert dfroi is not None
    dfmeta.insert(0, 'RoiID', np.int64(0))
    print dfmeta.dtypes.to_string()

    return dfmeta, dfvals, dfroi


def select(dfmeta, platename, acqname):
    cond = [dfmeta.experimentName == platename, dfmeta.plateName == acqname]
    return np.where(np.all(cond, axis=0))[0]


#####

cfg = config('input.yml')

# Nobody said it was easy....
# Sometimes the string 'null' is used instead of an empty string
dfargs = {'na_values': ['null'], 'keep_default_na': True}
#dfargs['nrows'] = 1000
dfmeta, dfvals, dfroi = get_dataframe(cfg, **dfargs)

# Hopefully all values are numeric
assert set(dfvals.dtypes) == {np.dtype('int64'), np.dtype('float64')}

scfg = cfg['server']
proxy = scfg.get('socksproxy', {})
client, session = connect(
    scfg['host'], scfg['user'], scfg['password'], proxy=proxy)

#####

screenimages = SPW(session, cfg['screenid'])

platename = 'X_110222_S1'
acqname = 'Meas_01'
indices = select(dfmeta, platename, acqname)

p = ProgressRecord(cfg['progresslist'])
for i in indices:
    print 'Row', i
    if 'r' not in p.get(i):
        meta = dfmeta.iloc[i]
        roi = dfroi.iloc[i]
        vals = dfvals.iloc[i]
        iid = screenimages.get_image(platename, acqname, meta.well)
        roi = create_roi(dfroi.iloc[i], iid)
        p.set(i, 'r')
    if 'f' not in p.get(i):
        ft = create_feature(dfmeta.iloc[i], dfvals.iloc[i])
        p.set(i, 'f')
