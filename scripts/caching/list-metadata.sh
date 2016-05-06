#!/bin/bash

# This script will dump a list of IDs for metadata caching for Screen
# Plate PlateAcquisition

date
OMERO_SERVER=~/OMERO.server
omero="$OMERO_SERVER/bin/omero"

$omero login

for objtype in Screen Plate PlateAcquisition; do
    echo "objtype:$objtype"
    out="$objtype.txt"
    $omero hql -q --limit -1 --style plain "SELECT id FROM $objtype" | \
        cut -d,  -f2 > "$out"
done
