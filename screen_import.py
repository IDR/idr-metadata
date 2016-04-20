#!/usr/bin/env python

from argparse import ArgumentParser
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import expanduser
from os.path import exists
from os.path import join
from subprocess import call


bin = expanduser("~/OMERO.server/bin/omero")
assert exists(bin)

parser = ArgumentParser()
parser.add_argument("screen")
parser.add_argument(
    "--force",
    action="store_true",
    default=False,
    help="Re-import if necessary"
)
ns = parser.parse_args()

command = [
    bin, "import", "--",
    "--checksum-algorithm=File-Size-64",
    "--transfer=ln_s"
]

if not ns.force:
    command += ["--exclude=clientpath"]

if ns.screen[-1] == "/":
    ns.screen = ns.screen[0:-1]

if "plates" in ns.screen:
    base, ignore = ns.screen.split("/plates/")
    plates = ns.screen
else:
    base = ns.screen
    plates = join(ns.screen, "plates", "*")

screen = basename(base)
study = basename(dirname(base))

print "Study: ", study
print "Screen: ", screen
print "Plate count:", len(glob(plates))
assert exists(ns.screen)

for plate in sorted(glob(plates)):
    if plate.endswith(".log"):
        continue
    if exists(plate + ".log"):
        print "Skipping due to %s.log" % plate
        continue
    name = basename(plate)
    with open(plate, "r") as f:
        target = f.read().strip()
    print name, "-->", target

    if call(command + [
            "--name=%s" % name,
            "--target=Screen:name:%s/%s" % (study, screen),
            target]):
        print "FAILED",
    else:
        print "PASSED",
    print "=" * 40
