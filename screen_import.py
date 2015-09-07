#!/usr/bin/env python

from argparse import ArgumentParser
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import expanduser
from os.path import exists
from os.path import join
from subprocess import check_call


bin = expanduser("~/OMERO.server/bin/omero")
assert exists(bin)

parser = ArgumentParser()
parser.add_argument("screen")
parser.add_argument("--force",
    action="store_true",
    default=False,
    help="Re-import if necessary")
ns = parser.parse_args()

command = [
      bin, "import", "--",
      "--checksum-algorithm=File-Size-64",
      "--transfer=ln_s"
]

if not ns.force:
    command += ["--exclude=filename"]

if ns.screen[-1] == "/":
    ns.screen = ns.screen[0:-1]

screen = basename(ns.screen)
study = basename(dirname(ns.screen))

print "Study: ", study
print "Screen: ", screen
assert exists(ns.screen)


plates = join(ns.screen, "plates", "*")
for plate in glob(plates):
    name = basename(plate)
    with open(plate, "r") as f:
        target = f.read().strip()
    print name, "-->", target

    check_call(command + [
      "--name=%s" % name,
      "--target=Screen:name:%s/%s" % (study, screen),
      "--transfer=ln_s", target]) 
