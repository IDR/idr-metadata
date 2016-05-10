#!/usr/bin/env python

from sys import stderr
from os.path import basename
from os.path import exists
from argparse import ArgumentParser

def get_lines():
    for i in ns.input:
        with open(i, "r") as f:
            path = f.read().strip()
            yield "%s\t%s" % (basename(i), path)

def main(output, inputs):
    existing = ()
    if exists(output):
        with open(output, "r") as out:
            existing = out.read().split("\n")

    with open(output, "a") as out:
        for line in get_lines():
            if line in existing:
                print >>stderr, "Dupe: ", line
            else:
                print >>out, line

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("input", nargs="+", help=(
        "Files which should be converted to TSV"
    ))
    ns = parser.parse_args()
    main(ns.output, ns.input)
