#!/usr/bin/env python

from collections import defaultdict
from fileinput import input
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import expanduser
from os.path import exists
from os.path import join
from sys import path
from sys import stderr


from omero import all  # noqa
from omero import ApiUsageException  # noqa
from omero.cli import CLI  # noqa
from omero.cli import Parser  # noqa
from omero.gateway import BlitzGateway  # noqa
from omero.rtypes import unwrap  # noqa
from omero.sys import ParametersI  # noqa
from omero.util.text import TableBuilder  # noqa
from omero.util.text import filesizeformat  # noqa

from yaml import load

def studies():
    with open("bulk.yml") as f:
        default_columns = load(f).get("columns", {})

    rv = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for study in sorted(glob("idr*")):
        if study[-1] == "/":
            study = study[0:-1]

        target = "Plate"
        containers = glob(join(study, "screen[ABC]"))
        if containers:
            assert not glob(join(study, "experiment*"))
        else:
            target = "Dataset"
            containers = glob(join(study, "experiment*"))

        assert containers >= 1
        for container in sorted(containers):
            bulk = glob(join(container, "*bulk.yml"))
            assert len(bulk) == 1, container
            bulk = bulk[0]
            pdir = dirname(bulk)
            with open(bulk, "r") as f:
                y = load(f)
            p = join(pdir, y["path"])
            columns = y.get("columns", default_columns)
            name_idx = None
            path_idx = None
            target_idx = None
            for idx, col in enumerate(columns):
               if col == "name":
                   name_idx = idx
               elif col == "target":
                   target_idx = idx
               elif col == "path":
                   path_idx = idx

            for line in input([p]):
                parts = line.strip().split("\t")
                if name_idx:
                    name = parts[name_idx]
                else:
                    if path_idx < len(parts):
                        name = basename(parts[path_idx])
                    else:
                        raise Exception(path_idx, container, bulk)
                if target_idx:
                    target = parts[target_idx]
                rv[study][container][target].append(name)
    for study, containers in sorted(rv.items()):
        for container, types in sorted(containers.items()):
            assert len(types) == 1, (study, container, types)
    return rv


def orphans(query):
    orphans = unwrap(query.projection((
        "select distinct f.id from Image i "
        "join i.fileset as f "
        "left outer join i.wellSamples as ws "
        "where ws = null "
        "order by f.id"), None))
    for orphan in orphans:
        print "Fileset:%s" % (orphan[0])
    print >>stderr, "Total:", len(orphans)


def unknown(query):
    on_disk = []
    for study, screens in sorted(studies().items()):
        for screen, plates in screens.items():
            on_disk.append(screen)
            on_disk.extend(plates)

    on_server = unwrap(query.projection((
        "select s.name, s.id from Screen s"), None))
    for name, id in on_server:
        if name not in on_disk:
            print "Screen:%s" % id, name

    on_server = unwrap(query.projection((
        "select s.name, p.name, p.id from Plate p "
        "join p.screenLinks as sl join sl.parent as s"), None))
    for screen, name, id in on_server:
        if name not in on_disk:
            print "Plate:%s" % id, name, screen


def check_search(query, search):
    obj_types = ('Screen', 'Plate', 'Image')
    print "loading all map annotations"
    res = query.findAllByQuery("from MapAnnotation m", None)
    all_values = set(
        v for m in res for k, v in m.getMapValueAsMap().iteritems()
    )
    print "searching for all unique values [%d]" % len(all_values)
    with open("no_matches.txt", "w") as fo:
        for v in all_values:
            try:
                matches = []
                for t in obj_types:
                    search.onlyType(t)
                    search.byFullText(v)
                    hit = search.hasNext()
                    matches.append(0 if not hit else len(search.results()))
                fo.write("%s\n" % '\t'.join(map(str, matches)))
            except ApiUsageException as e:
                stderr.write("%s: %s\n" % (v, e))
                continue


def stat_screens(query):

    tb = TableBuilder("Container")
    tb.cols(["ID", "Set", "Wells", "Images", "Planes", "Bytes"])

    plate_count = 0
    well_count = 0
    image_count = 0
    plane_count = 0
    byte_count = 0

    for study, containers in sorted(studies().items()):
        for container, set_expected in sorted(containers.items()):
            params = ParametersI()
            params.addString("container", container)
            if "Plate" in set_expected:
                expected = set_expected["Plate"]
                rv = unwrap(query.projection((
                    "select s.id, count(distinct p.id), "
                    "       count(distinct w.id), count(distinct i.id),"
                    "       sum(cast(pix.sizeZ as long) * pix.sizeT * pix.sizeC), "
                    "       sum(cast(pix.sizeZ as long) * pix.sizeT * pix.sizeC * "
                    "           pix.sizeX * pix.sizeY * 2) "
                    "from Screen s "
                    "left outer join s.plateLinks spl "
                    "left outer join spl.child as p "
                    "left outer join p.wells as w "
                    "left outer join w.wellSamples as ws "
                    "left outer join ws.image as i "
                    "left outer join i.pixels as pix "
                    "where s.name = :container "
                    "group by s.id"), params))
            elif "Dataset" in set_expected:
                expected = set_expected["Dataset"]
                rv = unwrap(query.projection((
                    "select p.id, count(distinct d.id), "
                    "       0, count(distinct i.id),"
                    "       sum(cast(pix.sizeZ as long) * pix.sizeT * pix.sizeC), "
                    "       sum(cast(pix.sizeZ as long) * pix.sizeT * pix.sizeC * "
                    "           pix.sizeX * pix.sizeY * 2) "
                    "from Project p "
                    "left outer join p.datasetLinks pdl "
                    "left outer join pdl.child d "
                    "left outer join d.imageLinks as dil "
                    "left outer join dil.child as i "
                    "left outer join i.pixels as pix "
                    "where p.name = :container "
                    "group by p.id"), params))
            else:
                raise Exception("unknown: %s" % set_expected.keys())

            if not rv:
                tb.row(container, "MISSING", "", "", "", "", "")
            else:
                for x in rv:
                    plate_id, plates, wells, images, planes, bytes = x
                    plate_count += plates
                    well_count += wells
                    image_count += images
                    if planes:
                        plane_count += planes
                    if bytes:
                        byte_count += bytes
                    else:
                        bytes = 0
                    if plates != len(expected):
                        plates = "%s of %s" % (plates, len(expected))
                    tb.row(container, plate_id, plates, wells, images, planes,
                           filesizeformat(bytes))
    tb.row("Total", "", plate_count, well_count, image_count, plane_count,
           filesizeformat(byte_count))
    print str(tb.build())


def stat_plates(query, screen, images=False):

    params = ParametersI()
    params.addString("screen", screen)

    obj = query.findByQuery((
        "select s from Screen s "
        "where s.name = :screen"), params)

    if not obj:
        raise Exception("unknown screen: %s" % screen)

    if images:
        q = ("select %s from Image i "
             "join i.wellSamples ws join ws.well w "
             "join w.plate p join p.screenLinks sl "
             "join sl.parent s where s.name = :screen")

        limit = 1000
        found = 0
        count = unwrap(query.projection(
            q % "count(distinct i.id)", params
        ))[0][0]
        print >>stderr, count
        params.page(0, limit)

        q = q % "distinct i.id"
        q = "%s order by i.id" % q
        while count > 0:
            rv = unwrap(query.projection(q, params))
            count -= len(rv)
            found += len(rv)
            params.page(found, limit)
            for x in rv:
                yield x[0]
        return

    plates = glob(join(screen, "plates", "*"))
    plates = map(basename, plates)

    tb = TableBuilder("Plate")
    tb.cols(["PID", "Wells", "Images"])

    well_count = 0
    image_count = 0
    for plate in plates:
        params.addString("plate", plate)
        rv = unwrap(query.projection((
            "select p.id, count(distinct w.id), count(distinct i.id)"
            "  from Screen s "
            "left outer join s.plateLinks spl join spl.child as p "
            "left outer join p.wells as w "
            "left outer join w.wellSamples as ws "
            "left outer join ws.image as i "
            "where s.name = :screen and p.name = :plate "
            "group by p.id"), params))
        if not rv:
            tb.row(plate, "MISSING", "", "")
        else:
            for x in rv:
                plate_id, wells, images = x
                well_count += wells
                image_count += images
                tb.row(plate, plate_id, wells, images)
    tb.row("Total", "", well_count, image_count)
    print str(tb.build())


def copy(client, copy_from, copy_type, copy_to):
    gateway = BlitzGateway(client_obj=client)
    print gateway.applySettingsToSet(copy_from, copy_type, [copy_to])
    gateway.getObject("Image", copy_to).getThumbnail(size=(96,), direct=False)


def main():
    parser = Parser()
    parser.add_login_arguments()
    parser.add_argument("--orphans", action="store_true")
    parser.add_argument("--unknown", action="store_true")
    parser.add_argument("--search", action="store_true")
    parser.add_argument("--images", action="store_true")
    parser.add_argument("--copy-from", type=long, default=None)
    parser.add_argument("--copy-type", default="Image")
    parser.add_argument("--copy-to", type=long, default=None)
    parser.add_argument("screen", nargs="?")
    ns = parser.parse_args()

    cli = CLI()
    cli.loadplugins()
    client = cli.conn(ns)
    try:
        query = client.sf.getQueryService()
        if ns.orphans:
            orphans(query)
        elif ns.unknown:
            unknown(query)
        elif ns.search:
            search = client.sf.createSearchService()
            check_search(query, search)
        elif not ns.screen:
            stat_screens(query)
        else:
            if ns.copy_to:
                copy(client, ns.copy_from, ns.copy_type, ns.copy_to)
            else:
                for x in stat_plates(query, ns.screen, ns.images):
                    print x
    finally:
        cli.close()

if __name__ == "__main__":
    main()
