#!/usr/bin/env python

from collections import defaultdict
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import expanduser
from os.path import exists
from os.path import join
from sys import path
from sys import stderr
from subprocess import call


lib = expanduser("~/OMERO.server/lib/python")
assert exists(lib)
path.insert(0, lib)

from omero import all
from omero.cli import CLI
from omero.cli import Parser
from omero.rtypes import unwrap
from omero.sys import ParametersI
from omero.util.text import TableBuilder


def stat_screens(query):
    studies = defaultdict(lambda: defaultdict(list))
    for study in glob("idr*"):
        if study[-1] == "/":
            study = study[0:-1]

        for screen in glob(join(study, "screen*")):
            for plate in glob(join(screen, "plates", "*")):
                studies[study][screen].append(basename(plate))

    tb = TableBuilder("Screen")
    tb.cols(["ID", "Plates", "Wells", "Images"])

    for study, screens in sorted(studies.items()):
        for screen, plates in screens.items():
            params = ParametersI()
            params.addString("screen", screen)
            rv = unwrap(query.projection((
                "select s.id, count(distinct p.id), count(distinct w.id), count(distinct i.id) from Screen s "
                "left outer join s.plateLinks spl "
                "left outer join spl.child as p "
                "left outer join p.wells as w "
                "left outer join w.wellSamples as ws "
                "left outer join ws.image as i "
                "where s.name = :screen "
                "group by s.id"), params))
            if not rv:
                tb.row(screen, "MISSING", "", "", "")
            else:
                for x in rv:
                    tb.row(screen, *x)
    print str(tb.build())


def stat_plates(query):

    screens = defaultdict(list)

    for screen in glob(join(study, "screen*")):
        for plate in glob(join(screen, "plates", "*")):
            screens[screen].append(basename(plate))

    tb = TableBuilder("Screen")
    tb.cols(["Plate", "SID", "PID", "Wells", "Images"])

    for screen, plates in screens.items():
        params = ParametersI()
        params.addString("screen", screen)

        screen = query.findByQuery((
            "select s from Screen s "
            "where s.name = :screen"), params)

        if not screen:
            tb.row("")

        for plate in plates:
            params.addString("plate", plate)
            rv = unwrap(query.projection((
                "select s.id, p.id, count(w.id), count(i.id) from Screen s "
                "left outer join s.plateLinks spl join spl.child as p "
                "left outer join p.wells as w "
                "left outer join w.wellSamples as ws "
                "left outer join ws.image as i "
                "where s.name = :screen and p.name = :plate "
                "group by s.id, p.id"), params))
            if not rv:
                tb.row(screen, plate, "MISSING", "", "" "" "")
            else:
                for x in rv:
                    tb.row(screen, plate, *x)
    print str(tb.build())

def main():
    parser = Parser()
    parser.add_login_arguments()
    parser.add_argument("choice", nargs="*", default="screen", choices=["plate", "screen"])
    ns = parser.parse_args()

    cli = CLI()
    cli.loadplugins()
    client = cli.conn(ns)
    try:
        query = client.sf.getQueryService()
        if ns.choice == "screen":
            stat_screens(query)
        elif ns.choice == "plate":
            stat_plates(query)
        else:
            raise Exception("unknown: %s" % ns.choice)
    finally:
        cli.close()

if __name__ == "__main__":
    main()
