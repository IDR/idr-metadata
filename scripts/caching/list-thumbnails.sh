#!/bin/bash

# This script will dump a list of image IDs from each screen to a file in
# the current directory (so you should cd into a new directory first)

date
OMERO_SERVER=~/OMERO.server
omero="$OMERO_SERVER/bin/omero"

$omero login

$omero hql 'select id,name from Screen' --limit -1 -q --style plain | \
    while IFS='' read -r line; do
        IFS=, read -a arr <<< "$line"
        echo "id:${arr[1]} name:${arr[2]}"

        # List all image IDs in each screen
        # Only use the first part of screen names (before '/') so there may
        # be multiple screens in the same thumbnails list file
        out="${arr[2]%/*}.txt"
        $omero hql -q --limit -1 --style plain "\
            SELECT ws.image.id \
            FROM WellSample ws, Plate p, ScreenPlateLink spl \
            WHERE spl.child=p AND ws.well.plate=p \
            AND spl.parent.id=${arr[1]}" | \
            cut -d,  -f2 >> "$out"
    done
