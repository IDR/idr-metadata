#!/usr/bin/env python

from collections import defaultdict
from fileinput import input
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from sys import stderr


from omero import all  # noqa
from omero import ApiUsageException  # noqa
from omero.cli import CLI  # noqa
from omero.cli import Parser  # noqa
from omero.gateway import BlitzGateway  # noqa
from omero.model import MapAnnotationI  # noqa
from omero.model import NamedValue
from omero.rtypes import rstring # noqa
from omero.rtypes import unwrap  # noqa
from omero.sys import ParametersI  # noqa
from omero.util.text import TableBuilder  # noqa
from omero.util.text import filesizeformat  # noqa

# Description
E_D = "Experiment Description"
P_T = "Publication Title"

# Map (also P_T)
S_T = ("Study Type", "Study Type")
I_T = ("Experiment Imaging Method", "Imaging Method")
P_A = ("Study Author List", "Publication Authors")
P_M = ("Study PubMed ID", "PubMed ID")
P_D = ("Study DOI", "Publication DOI")

def screen_metadata(client, file, object):
    query = client.sf.getQueryService()
    update = client.sf.getUpdateService()
    name, oid = object.split(":")
    do_update = False
    obj = query.findByQuery("select x from %s x join fetch x.annotationLinks xal join fetch xal.child where x.id = %d" % (name, long(oid)), None)
    ann = None
    for link in obj.copyAnnotationLinks():
        if isinstance(link.child, MapAnnotationI):
            if ann is not None:
                raise Exception("2 maps!")
            ann = link.child
            print "Found map:", ann.id.val
    if ann is None:
        ann = MapAnnotationI()
        ann.setMapValue(list())
        obj.linkAnnotation(ann)
        do_update = True
        print "Creating new map"

    old = unwrap(obj.description)
    desc = ""
    values = dict()
    for line in input([file]):
        parts = line.strip().split("\t")
        key = parts[0]
        if len(parts) > 1:
            val = parts[1]
        else:
            val = None
        if key == "Study " + P_T:
            desc += P_T
            desc += "\n"
            desc += val
            desc += "\n\n"
        elif key == E_D:
            desc += E_D
            desc += "\n"
            desc += val
        else:
            for x, y in (S_T, I_T, P_A, P_M, P_D):
                if key == x:
                    values[y] = val.strip('"')

    old_values = dict()
    for x in ann.getMapValue():
        old_values[x.name.val] = x
    for x, y in (S_T, I_T, P_A, P_M, P_D):
        if y not in old_values:
            ann.getMapValue().append(NamedValue(y, values[y]))
            do_update = True
            print "found new named value"
        elif old_values[y].value.val != values[y]:
            old_values[y].value = rstring(values[y])
            do_update = True
            print "changed named value"

    if old != desc:
        do_update = TRue
        obj.description = rstring(desc)
    else:
        print "descriptions match"

    if do_update:
        print "updating"
        update.saveObject(obj)
    print values


def main():
    parser = Parser()
    parser.add_login_arguments()
    parser.add_argument("file")
    parser.add_argument("object")
    ns = parser.parse_args()

    cli = CLI()
    cli.loadplugins()
    client = cli.conn(ns)
    try:
        screen_metadata(client, ns.file, ns.object)
    finally:
        cli.close()


if __name__ == "__main__":
    main()
