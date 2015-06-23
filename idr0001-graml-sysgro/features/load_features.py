#!/usr/bin/env python

import getpass
import numpy as np
import os
import pandas
import re
import yaml

import omero
import omero.clients
import omero.gateway
from omero.rtypes import rstring, unwrap
import features


FEATURE_NS = '/test/features'
FEATURE_ANN_NS = '/test/features/annotations'


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
            print 'Warning:File not found: %s' % self.filename
            # Assume this means file doesn't exist

    def _setcache(self, id, state):
        """
        Add a state to the cache
        """
        try:
            self.cache[str(id)].append(state)
        except KeyError:
            self.cache[str(id)] = [state]

    def set(self, id, state):
        """
        Append a state
        :param id: An identifier
        :param state: The state
        """
        with open(self.filename, 'a') as f:
            f.write('%s:%s\n' % (id, state))
        self._setcache(id, state)

    def get(self, id, prefix=None):
        """
        Retrieve states for an id
        :param id: An identifier
        :param prefix: Optional state prefix. If provided searches for states
               prefixed with '$prefix:' and returns the remainder
        """
        vals = self.cache.get(str(id), [])
        if not prefix:
            return vals
        r = []
        for v in vals:
            vs = v.split(':', 1)
            if vs[0] == prefix and len(vs) == 2:
                r.append(vs[1])
        return r

    def clear(self):
        """
        Delete the file
        """
        try:
            os.unlink(self.filename)
        except OSError as e:
            print 'Failed to delete %s: %s' % (self.filename, e)
        self.cache = {}


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
        ids = {}
        ids['plate'] = self.plates[platename]['id']
        ids['acq'] = self.plates[platename]['acquisitions'][acqname]['id']
        well = self.plates[platename]['acquisitions'][acqname]['wells'][(r, c)]
        ids['well'] = well['wid']
        ids['image'] = well['iid']
        return ids


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


def create_roi(session, coordstr, imageid):
    points = parse_coords(coordstr)
    poly = omero.model.PolygonI()
    pointstr = ' '.join('%d,%d' % p for p in points)
    poly.setPoints(rstring(pointstr))
    roi = omero.model.RoiI()
    roi.addShape(poly)
    im = omero.model.ImageI(imageid, False)
    roi.setImage(im)
    print 'create_roi %s... %s' % (points[:3], imageid)
    if session:
        roi = session.getUpdateService().saveAndReturnObject(roi)
    else:
        print 'Dry-run'
    return roi


def get_feature_table(session, screenid):
    qs = session.getQueryService()
    params = omero.sys.ParametersI()
    params.addId(screenid)
    params.addString('ns', FEATURE_ANN_NS)
    tid = qs.projection(
        'SELECT sal.child.file.id FROM ScreenAnnotationLink sal '
        'WHERE sal.child.class=FileAnnotation '
        'AND sal.child.ns=:ns AND sal.parent.id=:id', params)
    tid = unwrap(tid)
    assert len(tid) <= 1
    if tid:
        uid = session.getAdminService().getEventContext().userId
        fts = features.OmeroTablesFeatureStore.FeatureTable(
            session, '', FEATURE_NS, FEATURE_ANN_NS, uid, ofileid=tid[0][0])
        return fts
    return None


def create_feature_table(session, screenid, meta, vals):
    metadesc = [
        ('Plate', 'PlateID'),
        ('Well', 'WellID'),
        ('Image', 'ImageID'),
        ('Roi', 'RoiID'),
        ]

    for colname in meta:
        t = meta[colname].dtype.type
        if t in [np.str, np.string_, np.object_]:
            maxlen = max(meta[colname].str.len()) + 1
            metadesc.append(('String', colname, maxlen))
        else:
            raise Exception('Unexpected type: %s' % t)
    ftdesc = list(vals.columns)

    uid = session.getAdminService().getEventContext().userId
    fts = features.OmeroTablesFeatureStore.FeatureTable(
        session, 'FEATURES-TEST.h5', FEATURE_NS, FEATURE_ANN_NS, uid,
        noopen=True)
    fts.new_table(metadesc, ftdesc)
    fts.create_file_annotation(
        'Screen', long(screenid), FEATURE_ANN_NS,
        fts.get_table().getOriginalFile())
    return fts


def create_feature(fts, ids, ms, vs):
    print 'create_feature ids:[%s] meta:[%s] %s...' % (
        ids, ms.values, vs[:3].values)
    if fts:
        fts.store(pandas.concat([ids, ms]), vs, replace=False)
    else:
        print 'Dry-run'


def get_dataframe(cfg, **kwargs):
    dfmeta, dfvals, dfroi = load_features(
        cfg['features'], cfg['metadatacolumns'], cfg['roicolumn'], **kwargs)
    # print dfmeta.dtypes.to_string()
    # print dfvals.dtypes.to_string()
    # print dfroi.dtypes
    # print cfg

    # If this is meant to be a str column then get rid of np.nan
    for k, v in [kv for mc in cfg['metadatacolumns'] for kv in mc.iteritems()]:
        if v == 'str':
            dfmeta[k] = dfmeta[k].replace(np.nan, '')

    assert dfroi is not None
    # dfmeta.insert(0, 'RoiID', np.int64(0))
    # print dfmeta.dtypes.to_string()

    return dfmeta, dfvals, dfroi


def select(dfmeta, platename, acqname):
    cond = dfmeta.experimentName == platename
    if acqname :
        cond &= (dfmeta.plateName == acqname)

    return np.where(cond)[0]


def run(p, session, fts, dfmeta, dfroi, dfvals, platename, acqname):
    assert platename
    if not acqname:
        acqnames = screenimages.plates[platename]['acquisitions']
    else:
        acqnames = [acqname]
    for acqname in acqnames:
        print 'Acquistion', acqname
        indices = select(dfmeta, platename, acqname)
        for i in indices:
            print 'Row', i
            meta = dfmeta.iloc[i]
            ids = screenimages.get_image(platename, acqname, meta.well)
            if 'r' not in p.get(i):
                roi = dfroi.iloc[i]
                roi = create_roi(session, dfroi.iloc[i], ids['image'])
                p.set(i, 'r')
                if session:
                    p.set(i, 'r:%d' % unwrap(roi.id))
                else:
                    p.set(i, 'r:-1')
            if 'f' not in p.get(i):
                rid = long(p.get(i, 'r')[-1])
                metaids = [ids['plate'], ids['well'], ids['image'], rid]
                metaids = pandas.Series(
                    metaids, index=['PlateID', 'WellID', 'ImageID', 'RoiID'])
                create_feature(fts, metaids, dfmeta.iloc[i], dfvals.iloc[i])
                p.set(i, 'f')


#####

cfg = config('input.yml')

# Nobody said it was easy....
# Sometimes the string 'null' is used instead of an empty string
dfargs = {'na_values': ['null'], 'keep_default_na': True}
# dfargs['nrows'] = 1000
dfmeta, dfvals, dfroi = get_dataframe(cfg, **dfargs)

# Hopefully all values are numeric
assert set(dfvals.dtypes) == {np.dtype('int64'), np.dtype('float64')}

scfg = cfg['server']
proxy = scfg.get('socksproxy', {})
client, session = connect(
    scfg['host'], scfg['user'], scfg['password'], proxy=proxy)

client.enableKeepAlive(60)

#####

screenimages = SPW(session, cfg['screenid'])
# screenimages.print_all()

# Todo: Empty => automatically loop through all
platename = cfg['platename']
acqname = cfg['acqname']

args = [dfmeta, dfroi, dfvals, platename, acqname]
if cfg['dryrun']:
    p = ProgressRecord('dryrun-' + cfg['progresslist'])
    p.clear()
    run(p, None, None, *args)
else:
    fts = get_feature_table(session, cfg['screenid'])
    if not fts:
        fts = create_feature_table(session, cfg['screenid'], dfmeta, dfvals)
    p = ProgressRecord(cfg['progresslist'])
    run(p, session, fts, *args)
    fts.close()
