#!/usr/bin/env python

from collections import defaultdict
from glob import glob
from re import compile

X_s = defaultdict(lambda: 0)
Y_s = defaultdict(lambda: 0)
PAT = compile(r".*?field--X(\d+)--Y(\d+).*?")

with open("raw", "r") as f:
    plates = f.read().strip().split("\n")

for plate in plates:
    for file in glob(plate + "/*"):
        m = PAT.match(file)
        if not m:
            raise Exception(file)
        x = int(m.group(1))
        y = int(m.group(2))
        X_s[x] += 1
        Y_s[y] += 1

for k, v in sorted(X_s.items()):
    print(k, v)

for k, v in sorted(Y_s.items()):
    print(k, v)
