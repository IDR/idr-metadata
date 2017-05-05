#!/usr/bin/env python

"""
Utility for managing map-annotations
"""

import omero
from omero.model import MapAnnotationI, NamedValue
from omero.rtypes import rstring


def create_map_annotation(targets, rowkvs, ns):
    ma = MapAnnotationI()
    ma.setNs(rstring(ns))
    mv = []
    for k, vs in rowkvs:
        if not isinstance(vs, (tuple, list)):
            vs = [vs]
        mv.extend(NamedValue(k, str(v)) for v in vs)

    if not mv:
        raise Exception('Empty MapValue')

    ma.setMapValue(mv)

    links = []
    for target in targets:
        otype = target.ice_staticId().split('::')[-1]
        link = getattr(omero.model, '%sAnnotationLinkI' % otype)()
        link.setParent(target)
        link.setChild(ma)
        links.append(link)
    return links
